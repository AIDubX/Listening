from tts.infer_cli import *
from app.utils.pack_audio import pack_ogg,speed_change,pack_wav,read_clean_buffer
from loguru import logger
from io import BytesIO
import gc

class MegaTTS3DiTInfer(MegaTTS3DiTInfer):

    def forward(self, resource_context, input_text, time_step=25, p_w=0.5, t_w=0.5,stream=False,format="ogg",speed=1.0):
        device = self.device
        audio_bytes = BytesIO()
        dur_disturb=0.1
        dur_alpha=1.0
        ph_ref = resource_context['ph_ref'].to(device)
        tone_ref = resource_context['tone_ref'].to(device)
        mel2ph_ref = resource_context['mel2ph_ref'].to(device)
        vae_latent = resource_context['vae_latent'].to(device)
        ctx_dur_tokens = resource_context['ctx_dur_tokens'].to(device)
        incremental_state_dur_prompt = resource_context['incremental_state_dur_prompt']

        with torch.inference_mode():
            ''' Generating '''
            wav_pred_ = []
            language_type = classify_language(input_text)
            if language_type == 'en':
                input_text = self.en_normalizer.normalize(input_text)
                text_segs = chunk_text_english(input_text, max_chars=130)
            else:
                input_text = self.zh_normalizer.normalize(input_text)
                text_segs = chunk_text_chinesev2(input_text, limit=60)

            for seg_i, text in enumerate(text_segs):
                ''' G2P '''
                ph_pred, tone_pred = g2p(self, text)
            
                ''' Duration Prediction '''
                mel2ph_pred = dur_pred(self, ctx_dur_tokens, incremental_state_dur_prompt, ph_pred, tone_pred, seg_i, dur_disturb, dur_alpha, is_first=seg_i==0, is_final=seg_i==len(text_segs)-1)
                
                inputs = prepare_inputs_for_dit(self, mel2ph_ref, mel2ph_pred, ph_ref, tone_ref, ph_pred, tone_pred, vae_latent)
                # Speech dit inference
                with torch.cuda.amp.autocast(dtype=self.precision, enabled=True):
                    x = self.dit.inference(inputs, timesteps=time_step, seq_cfg_w=[p_w, t_w]).float()
                
                # WavVAE decode
                x[:, :vae_latent.size(1)] = vae_latent
                wav_pred = self.wavvae.decode(x)[0,0].to(torch.float32)
                
                ''' Post-processing '''
                # Trim prompt wav
                wav_pred = wav_pred[vae_latent.size(1)*self.vae_stride*self.hop_size:].cpu().numpy()
                # Norm generated wav to prompt wav's level
                meter = pyln.Meter(self.sr)  # create BS.1770 meter
                loudness_pred = self.loudness_meter.integrated_loudness(wav_pred.astype(float))
                wav_pred = pyln.normalize.loudness(wav_pred, loudness_pred, self.loudness_prompt)
                if np.abs(wav_pred).max() >= 1:
                    wav_pred = wav_pred / np.abs(wav_pred).max() * 0.95

                if stream:
                    wav_pred = wav_pred.astype(float)
                    wav_pred = (wav_pred * 32767).astype(np.int16)
                    if speed != 1.0:
                        wav_pred = speed_change(wav_pred, speed, self.sr)
                    
                    audio_bytes = pack_ogg(audio_bytes, wav_pred, self.sr)
                    audio_bytes, audio_chunk = read_clean_buffer(audio_bytes)
                    yield audio_chunk
                else:
                    
                    wav_pred_.append(wav_pred)
            
            if not stream:
                # Combine audi
                wav_pred = combine_audio_segments(wav_pred_, sr=self.sr).astype(float)
                wav_pred = (wav_pred * 32767).astype(np.int16)
                if speed != 1.0:
                    wav_pred = speed_change(wav_pred, speed, self.sr)
                if format == "wav":
                    yield pack_wav(audio_bytes,wav_pred, self.sr)
                else:
                    yield pack_ogg(audio_bytes, wav_pred, self.sr).getvalue()
        gc.collect()
        torch.cuda.empty_cache()

infer_pipe = MegaTTS3DiTInfer()


def get_tts_wav(text, inp_audio_path, inp_npy_path, infer_timestep=32, p_w=1.6, t_w=2.5,stream=False,format="ogg",speed=1.0):
    with open(inp_audio_path, 'rb') as file:
        file_content = file.read()
    resource_context = infer_pipe.preprocess(file_content, latent_file=inp_npy_path)
    return infer_pipe.forward(resource_context, text, time_step=infer_timestep, p_w=p_w, t_w=t_w,stream=stream,format=format,speed=speed)

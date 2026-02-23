# 假设的 thin_roles_rule 函数实现
# from about_help import logger
import random
import re

try:
    import regex
except ImportError:
    pass

heroineRoleValue = "①|【女性主角】|"
actorprotagonistRoleValue = "②|【男性主角】|男主|"
girlRoleValue = "③|【女性少年】|♀㊣|女[孩娃童]|丫头|少女|小(兔子|姑娘|[环])"
boyRoleValue = "④|【男性少年】|♂㊣|男[孩娃童]|少年|鼻涕娃|放牛娃|小(娃子|家伙|朋友|[孩])"
#  默认女性老年，此参数可以修改，保留两边的英文双引号
seniorfemaleRoleValue = "⑤|【女性老年】|♀↑|祖母|姥姥|皇?太后|[外婆]婆|[舅伯]?[妈母娘]亲?(?!蛋|耶|呀|哎|嘞|啊|诶|炮|腔|的|了|子|女|俩|家|鸡|猪|猫|牛|婴|乳|爱|校|公司|老虎|亲[节河]|语|体|胎|性|纸|巾|疼|痛)|[姨姑婶](?!父|夫|丈|爷|爹|家|妈|[纸巾疼痛])|老(娘们|女人)|红缨长老|堂娜|(?<!少)奶奶"
#  默认男性老年，此参数可以修改，保留两边的英文双引号
seniormaleRoleValue = "⑥|【男性老年】|♂↑|爷爷|祖父|姥爷|外公|公公|丈人|[舅伯父爷叔](?![服子家奶姥婆妈母娘哥孙们青侄女俩爵乐特克明仲牙])|[姨姑][父夫丈爷]|老(.?头|丈|汉|爷|者|革命|药子|先生)|元帅|将军|司令|主席|教授|太上皇|太爷|大师|长老|掌柜|天[王帝]|[皇王][帝上]|掌门|门主|会长|族长|巫师|和尚|张子真|小狗|肖恩|周一仙|图麻骨|万剑一"
#  默认女性青年，此参数可以修改，保留两边的英文双引号
youngadultfemaleRoleValue = "⑦|【女性青年】|她|女[人生子朋友士郎性声王皇]|小姐|少(奶奶|妇)|媳妇|老婆|妇|嫂|[小老妹]妹|姑娘|[天皇帝]后|妃|[郡宫公女]主|仙子|女(秘书|经理|老板|教师|医生|律师|工程师|演员|舞者"
youngadultfemaleRoleValue += "|运动员|歌手|导演|制片人|记者|作家|摄影师|模特|设计师|厨师|销售|司机|警察|消防员|军人|志愿者|教练|主播|职员|职工|员工|企业家|华侨|元帅|将军|执事|护法)|保姆|银行柜员|美容师|服务员|空姐|"
youngadultfemaleRoleValue += "[王李张刘陈杨黄赵吴周徐孙马朱胡郭何林高罗郑梁谢宋唐许邓韩冯曹彭曾肖田董潘袁蔡蒋余于杜叶程魏苏吕丁任卢姚沈钟姜崔谭陆范汪廖石金韦贾夏付方邹熊白孟秦邱侯江尹薛闫段雷龙黎史陶贺毛郝顾龚邵万覃武钱戴严欧莫孔向汤常温康"
youngadultfemaleRoleValue += "施文牛樊葛邢安齐易乔伍庞颜倪庄聂章鲁岳翟殷詹申欧耿关兰焦俞左柳甘祝包宁尚符舒阮柯纪梅童凌毕单季傅伊上官诸葛慕容司马欧阳][一-龥]?"
youngadultfemaleRoleValue += "[爱蓓璧冰彩婵纯春聪翠黛丹娣娥铒芳菲芬枫凤馥红桂荷花惠慧姬佳姣洁婕锦瑾菁静晶菊娟可兰岚澜荔丽莉莲琳玲灵露璐美梅眉妹梦淼娜宁凝萍琪琦倩茜巧琴琼秋蓉柔蕊莎珊舒淑爽素婷婉琬纨薇熙霞娴香霄欣馨秀萱璇雪娅雅雁妍艳燕瑶怡伊滢英颖莹影莺毓羽媛瑗苑悦月芸韵昭珍枝芝芷竹珠紫]|阴姬|夏树之恋|花语|"
youngadultfemaleRoleValue += "维多利亚|浅野凉|凉酱|灵熙|妙藤|安妮|安楪祈|薇妮|爱玛|小环|小白|金瓶儿|苏茹|水月|文敏|幽姬|燕虹|天狐|(?<!老)(太太|夫人)"
#  默认男性青年，此参数可以修改，保留两边的英文双引号
youngadultmaleRoleValue = "⑧|【男性青年】|♂↓|△|他|男(生|子|人|朋友)|丈夫|先生|少爷|哥|兄弟|[省部厅局司县处科镇乡村军师旅团营连排班队园院校所警厂学组]长|[片武交乘]警|警[察司官卫员]|[军法长]官|书记|秘书|导演|教练|管理员|员工|[王皇天公]"
youngadultmaleRoleValue += "子|衙内|执事|方士|护法|小伙|青年|中年|大汉|和尚|书生|[肥柱楞锁彪牤]子|[王李张刘陈杨黄赵吴周徐孙马朱胡郭何林高罗郑梁谢宋唐许邓韩冯曹彭曾肖田董潘袁蔡蒋余于杜叶程魏苏吕丁任卢姚沈钟姜崔谭陆范汪廖石金韦贾夏付方邹熊白孟秦邱侯江尹薛闫段雷龙黎史陶贺毛郝顾龚邵万覃武钱戴严欧莫孔向汤常温康施文牛樊葛邢安齐易乔伍庞颜倪庄聂章鲁岳翟殷詹申欧耿关兰焦俞左柳甘祝包宁尚符舒阮柯纪梅童凌毕单季傅伊上官诸葛慕容司马欧阳][一-龥]?[奥傲邦保豹宝斌彬博策昌辰宸晨城淳郴聪达德迪栋冬东凡帆丰峰锋风富傅工公冠光国海翰航昊浩豪贺恒衡洪宏鸿华晖辉嘉坚建健强杰晶靖"
youngadultmaleRoleValue += "景俊浚凯楷奎魁坤昆朗梁良霖林龙隆民明铭鸣南楠鹏平齐祺棋奇乾谦庆权泉然仁睿瑞尚少森盛圣生胜书顺松颂泰涛韬天霆廷韦伟威巍卫玮锡翔祥新鑫兴星雄旭宣轩玄岩炎晏阳洋耀烨翼毅奕义永勇宇煜元远岳赟运允展章哲喆震振峥征智志焯卓潇]|汤姆|那人|(这|那|个|的)家伙|大夫(?!人)|老大|[大二三]少|魔眼|高山流水|良臣|胖子|山河永存|灵拓|灵钧|天下归火|火师之耻|寇北月|夏侯|翟菜|风神之翼|林惊羽|田不易|小灰|道玄|林惊羽|普泓|云易岚|萧逸|普智|玉阳子|青龙|曾叔常|万剑一|法相|普德|大黄|李洵|霸刀|费米"
#  默认女性中年，此参数可以修改，保留两边的英文双引号
olderadultfemaleRoleValue = "⑨|【女性中年】|️|♀☆|妈妈|妈|母亲|中年女人|嫂子|阿姨|婶"
#  默认男性中年，此参数可以修改，保留两边的英文双引号
olderadultmaleRoleValue = "⑩|【男性中年】|♂☆|爸|爹|父亲|中年男人|中年男子|黑袍中年|叔|伯|舅"
#  默认对话角色，此参数不要修改
dialogueRoleValue = ""
#  所有标签tag数组及所有默认角色规则数组
diyList = {"dialogue": {"name": "对话🗣️", "value": dialogueRoleValue},
           "heroine": {"name": "①女性主角👸🏻", "value": heroineRoleValue},
           "actorprotagonist": {"name": "② 男性主角🤴🏻", "value": actorprotagonistRoleValue},
           "girl": {"name": "③ 女性少年👧🏻", "value": girlRoleValue},
           "boy": {"name": "④ 男性少年👦🏻", "value": boyRoleValue},
           "seniorfemale": {"name": "⑤ 女性老年👵🏻", "value": seniorfemaleRoleValue},
           "seniormale": {"name": "⑥ 男性老年👴🏻", "value": seniormaleRoleValue},
           "youngadultfemale": {"name": "⑦ 女性青年👩🏻", "value": youngadultfemaleRoleValue},
           "youngadultmale": {"name": "⑧ 男性青年👨🏻", "value": youngadultmaleRoleValue},
           "olderadultfemale": {"name": "⑨ 女性中年🤵🏻‍♀️", "value": olderadultfemaleRoleValue},
           "olderadultmale": {"name": "⑩ 男性中年🤵🏻‍♂️", "value": olderadultmaleRoleValue}}
# 默认正则(旁白在前)
narration_front_regex = '[^”\"]{0,10}(?<!((__ALLROLE__)[^”\"？！。，\,\.\!\?传听]{0,20}|(把(?!门|手)|将(?!来)|跟|给|对|朝|向|盯着|望着|指着|打断|冲|拉|看(?!门|守|护)|见到|瞅|问|发现|理会)[^”\"]{0,20}的[一-龥]{0,3}|'
narration_front_regex += '(把(?!门|手)|将(?!来)|跟|给|对|朝|向|着|打断|冲|拉|看(?!门|守|护)|见|[找遇提飞想走爬接追]到|审视|瞅|望|问|(?<!传来|听到|听见)了|(?<!现|好)在(?![一-龥]{1,5}的[一-龥]{0,2}(__ROLE__))|像|往|一下|一指|住(?!的|着)|入(?!口|门)|发现|理会|知道|难为|替|等|视|被|与|吻|抓|摸)[一-龥]{0,8})[一-龥]{0,2})(__ROLE__)(?!.{0,50}(只听|听到|听见|传来[一-龥]{0,10}((__ALLROLE__)|声|音|嚎|叫|咆哮|娇叱)|[，。？！…][一-龥]{0,10}(?<!(把(?!门|手)|将(?!来)|跟|给|对|朝|向|着|打断|冲|拉|看(?!门|守|护)|见|[找遇提飞想走爬接追]到|审视|瞅|望|问|(?<!传来|听到|听见)了|(?<!现|好)在(?![一-龥]{1,5}的[一-龥]{0,2}(__ROLE__))|像|一下|一指|住(?!的|着)|入(?!口|门)|发现|理会|知道|替|等|视|被|与|吻|抓|摸)[一-龥]{0,5})(__ALLROLE__)))'
# 默认正则(旁白在后)
narration_back_regex = "[^”\"]{0,10}(?<!((__ALLROLE__)[^”\"]{0,100}[^？！。，\,\.\!\?传听]|(__ALLROLE__)[^”\"传听]{0,100}[，。？！…]|(把(?!门|手)|将|跟|给|对|朝|向|盯着|望着|指着|打断|冲|拉|看(?!门|守|护)|见到|瞅|问|发现|理会)[^”\"]{0,20}的[一-龥]{0,3}|(把(?!门|手)|将|跟|给|对|朝|向|着|打断|冲|拉|看(?!门|守|护)|见|[找遇提飞想走爬接追]到|审视|瞅|望|问|(?<!传来|听到|听见)了|(?<!现|好)在(?![一-龥]{1,5}的[一-龥]{0,2}(__ROLE__))|像|往|一下|一指|住(?!的|着)|入(?!口|门)|发现|理会|知道|难为|替|等|视|被|与|吻|抓|摸)[一-龥]{0,8})[一-龥]{0,2})(__ROLE__)(?!.{0,15}(只听|听到|听见|传来[一-龥]{0,10}((__ALLROLE__)|声|音|嚎|叫|咆哮|娇叱)))"


#  替换正则中的__ALLROLE__


#  最近一次对话角色参数


class CharacterRecognition:
    randomOrInOrder = 2  # 1 随机，2 按顺序，轮流
    randomOrFixed = 2  # 1 随机，2 固定选择第一个
    appendRoleMethod = 1  # 0  禁止追加角色功能，1 默认角色规则，2 基础角色标志规则
    DiaRule = 2  # 0 默认对话角色 ，1 最近一次对话角色，2 倒数第二个对话角色，3 所有角色配置随机播放
    fixedRoles = 1  # = 0 不固定，= 1 固定
    useAllRole = False

    def __init__(self, tags_data):
        self.hisTtsId = 0
        #  临时文本数组;
        self.historicalTextList = []
        #  历史对话 ID数组
        self.historicalDialogueIdList = []
        self.tmp_role_list = []
        self.tmp_list = None

        self.tags_data = tags_data
        self.append_rule()
        # self.append_rule()

    def thin_roles_rule(self, value):
        # 这里应该是精简角色规则的逻辑
        # 由于具体逻辑未给出，此处仅做示例
        return value.replace(r'[①②③④⑤⑥⑦⑧⑨⑩].*[★㊣↑↓☆]', r'\1').replace(r'[\u4e00-\u9fa5]', '一-龥')

    def get_role_str(self, roles):
        # 去除多余空格、换行，并规范竖线分隔符
        role_str = regex.sub(r'\|\n\s*|\s+', '|', str(roles)).strip('|')
        # 分割字符串得到角色名列表
        tmp_roles = role_str.split('|')
        # 使用集合去除重复项，然后重新组合成字符串
        diy_role = '|'.join(set(tmp_roles))
        return diy_role

    def get_tmp_role_list(self, tmp_list, tags_data, tmp_role_list, append_role_method):

        for i in range(len(tmp_list)):
            add_role = ""
            add_flag = "dialogue"

            # Check against default role
            if tmp_list == self.tags_data['dialogue']['defaultRole']:
                if 'defaultRole' in self.tags_data['dialogue']:
                    add_role = ""
                    add_flag = self.tags_data['dialogue']['defaultRole'][i]['value']

            # Check against roles and handle various conditions
            elif tmp_list == self.tags_data['dialogue']['role']:
                if 'defaultRole' in self.tags_data['dialogue']:
                    b = False
                    for j in range(len(self.tags_data['dialogue']['defaultRole'])):
                        if tmp_list[i]['id'] == self.tags_data['dialogue']['defaultRole'][j]['id']:
                            a = j
                            b = True
                            break

                    if ('defaultRole' not in self.tags_data['dialogue'] or not b) and (
                            'role' not in self.tags_data['dialogue'] or not self.tags_data['dialogue']['role'][i][
                        'value']):
                        add_role = ""
                        add_flag = "dialogue"
                    elif ('role' not in self.tags_data['dialogue'] or 'value' not in self.tags_data['dialogue']['role'][
                        i] or not
                          self.tags_data['dialogue']['role'][i]['value']) and (
                            'defaultRole' in self.tags_data['dialogue'] and b):
                        add_role = ""
                        # logger.debug(a)
                        # logger.debug(self.tags_data['dialogue']['defaultRole'][a]['value'])
                        add_flag = self.tags_data['dialogue']['defaultRole'][a]['value']
                    elif self.tags_data['dialogue']['role'][i]['value'] and (
                            'defaultRole' not in self.tags_data['dialogue'] or not b):
                        add_role = self.tags_data['dialogue']['role'][i]['value']
                        add_flag = "dialogue"
                    elif self.tags_data['dialogue']['role'][i]['value'] and b:
                        add_role = self.tags_data['dialogue']['role'][i]['value']
                        # logger.debug(a)
                        # logger.debug(self.tags_data['dialogue']['defaultRole'][a]['value'])
                        add_flag = self.tags_data['dialogue']['defaultRole'][a]['value']

            add_role = self.get_role_str(add_role)  # Assuming get_role_str is defined elsewhere

            # Construct tmpRoleValue based on conditions
            if add_role and add_flag != "dialogue":
                if append_role_method == 1:
                    tmp_role_value = f"{add_role}|{diyList[add_flag]['value']}"
                elif append_role_method == 2:
                    tmp_role_value = f"{add_role}|{self.thin_roles_rule(diyList[add_flag]['value'])}"
            elif add_role and add_flag == "dialogue":
                tmp_role_value = add_role
            else:
                if append_role_method == 1:
                    # logger.debug(f'add_flag: {add_flag} diylist: {diyList}')
                    if add_flag: tmp_role_value = diyList[add_flag]['value']
                elif append_role_method == 2:
                    tmp_role_value = self.thin_roles_rule(diyList[add_flag]['value'])

            if tmp_role_value:
                tmp_list[i]['value'] = tmp_role_value
                tmp_role_list.append(tmp_list[i])

        # logger.error(tmp_role_list)
        return tmp_role_list

    def get_default_voice_id(self):
        # 这里应该是获取默认语音 ID 的逻辑
        # logger.debug(f"default_voice: {default_voice}")
        voice_ids = []
        a = 0

        # 循环获取 defaultVoice 中为 "true" 的属性，并添加到 voiceIDs 列表的最后
        for item in self.tags_data['dialogue']['defaultFlag']:
            if item.get('value'):
                voice_ids.append(item)

        # 如果 voiceIDs 列表个数大于 0，则运行以下代码，否则返回 -1
        if voice_ids:
            # 如果只有一个，则返回这一个的 ID
            if len(voice_ids) == 1:
                return voice_ids[0].get('id')
            else:
                if self.randomOrInOrder == 1:
                    # 如果 voiceIDs 列表存在多个，则随机选择一个
                    return random.choice(voice_ids).get('id')
                if self.randomOrInOrder == 2:

                    if self.historicalDialogueIdList:
                        for i, voice_id in enumerate(voice_ids):
                            if self.historicalDialogueIdList[-1] == voice_id.get('id'):
                                a = i + 1
                        if self.randomOrFixed == 1:
                            if a == 0:
                                return random.choice(voice_ids).get('id')
                        return voice_ids[a].get('id')
        else:
            return -1

    def get_match_regex_flag(self, role_value, allrole_str, regex_str, str_to_match):
        # logger.debug(f"get_match_regex_flag: {role_value},{allrole_str},{str_to_match}")
        # 检查输入是否为空
        if not role_value or not regex_str or not str_to_match or regex_str == -1:
            return False

        # 去除role_value中的换行符
        tmp_role_value = regex.sub(r'\n', '', role_value)
        str_to_match = regex.sub(r'\n', '', str_to_match)

        # 如果tmp_role_value为空，返回false
        if not tmp_role_value:
            return False

        # 把regex_str中的 "__ROLE__" 替换成 tmp_role_value
        tmp_regex_str = regex_str.replace("__ROLE__", tmp_role_value)

        # 如果allrole_str不为空，把 "__ALLROLE__" 替换成 allrole_str
        if allrole_str:
            tmp_regex_str = tmp_regex_str.replace("__ALLROLE__", allrole_str)

        # 使用tmp_regex_str正则表达式匹配str_to_match
        if tmp_regex_str:
            try:
                if regex.search(tmp_regex_str, str_to_match):
                    return True
            except:
                print(tmp_regex_str)
                input()
                return False

        return False

    def get_tag_idx_by_voice_id(self, tag, voice_id):
        # 如果tag未定义，返回-1
        if tag is None:
            return -1
        # 遍历tag列表，寻找voice_id匹配项并返回其索引
        for i, item in enumerate(tag):
            if voice_id == item.id:
                return i
        # 未找到匹配项，返回-1
        return -1

    def get_tag_value_by_index(self, tag, index):
        # 如果index小于0或tag未定义，则返回空字符串
        if index < 0 or tag is None:
            return ""
        else:
            # 否则返回tag列表中index对应的value值
            return tag[index].get("value", "")

    def match_role(self, pre_text_flag, narr_text, roles, all_role_str, f_regexs, b_regexs):
        tmp_id_list = []
        for role in roles:
            _regex = -1
            # logger.error(role)
            if not role.get("value"):
                continue
            if pre_text_flag:
                _regex = self.get_tag_idx_by_voice_id(f_regexs, role['id'])

                if _regex == -1:
                    _regex = narration_front_regex
            else:

                _regex = self.get_tag_idx_by_voice_id(b_regexs, role['id'])
                if _regex == -1:
                    _regex = narration_back_regex

            # role_value, allrole_str, regex_str, str_to_match
            flag = self.get_match_regex_flag(role['value'], all_role_str, _regex, narr_text)

            if flag:
                if self.fixedRoles == 0:
                    tmp_id_list.append(role)
                else:
                    # todo: 返回情感
                    return role['id']

        if self.fixedRoles == 0:
            return self.get_default_voice_id(tmp_id_list)
        else:
            return -1

    def get_closest_narration(self, text_list, dialogue_index):
        closest_narration_before_index = -1
        closest_narration_after_index = -1

        # 寻找指定索引前的最近叙述
        for i in range(dialogue_index - 1, -1, -1):
            if text_list[i]["tag"] == "narration":
                tmp_value = regex.sub(r"^(\\s|\p{C}|\p{P}|\p{Z}|\p{S})+$", "", text_list[i]["text"])
                # print(tmp_value)
                if tmp_value != "":
                    closest_narration_before_index = i
                    break

        # 寻找指定索引后的最近叙述
        for i in range(dialogue_index + 1, len(text_list)):
            if text_list[i]["tag"] == "narration":
                tmp_value = regex.sub(r"^(\\s|\p{C}|\p{P}|\p{Z}|\p{S})+$", "", text_list[i]["text"])
                if tmp_value != "":
                    closest_narration_after_index = i
                    break

        # 确定最近的叙述索引
        if closest_narration_before_index == -1 and closest_narration_after_index != -1:
            closest_narration_index = closest_narration_after_index
        elif closest_narration_before_index != -1 and closest_narration_after_index == -1:
            closest_narration_index = closest_narration_before_index
        elif closest_narration_before_index != -1 and closest_narration_after_index != -1:
            closest_narration_index = dialogue_index - closest_narration_before_index if dialogue_index - closest_narration_before_index <= closest_narration_after_index - dialogue_index else closest_narration_after_index

        # 返回结果
        if closest_narration_index != -1:
            return {"content": text_list[closest_narration_index]["text"], "index": closest_narration_index}
        return None

    def default_dialogue_id(self):
        voice_ids = []
        for flag in self.tags_data['dialogue']['defaultFlag']:
            if flag["value"] == "true":
                voice_ids.append(flag)

        if len(voice_ids) > 2:
            a = b = c = 0
            historical_dialogue_id_list = []  # 假设self.historicalDialogueIdList已经定义并有相应数据

            for item in voice_ids:
                if 1 <= len(historical_dialogue_id_list) and historical_dialogue_id_list[-1] == item["id"]:
                    a = 1
                if 2 <= len(historical_dialogue_id_list) and historical_dialogue_id_list[-2] == item["id"]:
                    b = 2
                if 3 <= len(historical_dialogue_id_list) and historical_dialogue_id_list[-3] == item["id"]:
                    c = 5

            return a + b + c
        else:
            return -1

    def set_voice_id(self, lst, id_):
        for item in lst:
            if item.get('tag') == 'dialogue':
                item['id'] = id_
        return lst

    def append_rule(self):

        self.default_flags = self.tags_data['dialogue'].get('defaultFlag', [])
        # 获取默认的发音人
        self.default_tts_id = self.get_default_voice_id()

        if 0 < self.appendRoleMethod <= 3:
            # 初始化临时角色列表

            # 根据 tagsData 中 'dialogue' 的 'role' 和 'defaultRole' 存在与否来处理
            if 'role' not in self.tags_data['dialogue'] and 'defaultRole' not in self.tags_data['dialogue']:
                pass
            elif 'defaultRole' not in self.tags_data['dialogue'] and 'role' in self.tags_data['dialogue']:
                # logger.debug("追加 1 ")
                tmp_list = self.tags_data['dialogue']['role']
                tmp_role_list = self.get_tmp_role_list(tmp_list, self.tags_data, self.tmp_role_list,
                                                       self.appendRoleMethod)
            elif 'role' not in self.tags_data['dialogue'] and 'defaultRole' in self.tags_data['dialogue']:
                # logger.debug("追加 2 ")
                tmp_list = self.tags_data['dialogue']['defaultRole']
                tmp_role_list = self.get_tmp_role_list(tmp_list, self.tags_data, self.tmp_role_list,
                                                       self.appendRoleMethod)
            else:
                # logger.debug("追加 3 ")
                tmp_list = self.tags_data['dialogue']['role']
                tmp_role_list = self.get_tmp_role_list(tmp_list, self.tags_data, self.tmp_role_list,
                                                       self.appendRoleMethod)
                # 确保不在默认角色中重复追加角色
                for i in range(len(tmp_role_list)):
                    for j in range(len(self.tags_data['dialogue']['defaultRole'])):
                        if tmp_role_list[i]['id'] == self.tags_data['dialogue']['defaultRole'][j]['id']:
                            self.tags_data['dialogue']['defaultRole'].pop(j)
                            break  # 假设找到匹配项后不需要继续循环
                tmp_list = self.tags_data['dialogue']['defaultRole']
                tmp_role_list = self.get_tmp_role_list(tmp_list, self.tags_data, tmp_role_list, self.appendRoleMethod)

            # logger.debug(f"{self.tags_data['dialogue']['role']}")

    def handle_text(self, text):
        text_list = []
        tmp_str = ""
        end_tag = "narration"
        flag = 0

        # 按字符历遍来源文本，以区分对话和旁白，并把它们分开
        for index, i in enumerate(text):
            # tmp_str += char
            if i == "":
                continue
            if flag == 0 and (i == '"' or i == "“" or i == "「"):
                tmp_str = tmp_str.strip()
                if tmp_str != "" and re.sub(r"\W+", "", tmp_str):
                    text_list.append(
                        {"tag": "narration", "text": tmp_str})
                tmp_str = i
                flag = 1
                continue
            elif flag == 1 and (i == "”" or i == '"' or i == "」"):
                if tmp_str[-1] not in ["。", "！", "？", ".", "!", "?", "~", "…"]:
                    tmp_str += i
                    flag = 2
                    continue
                flag = 0
                text_list.append({"tag": "dialogue", "text": (tmp_str + i).strip()})
                tmp_str = ""
                continue
            elif flag == 2:
                if len(text_list) > 0:
                    text_list[-1]["text"] += tmp_str
                    tmp_str = ""
                if i == '"' or i == "“" or i == "「":
                    tmp_str = tmp_str.strip()
                    if tmp_str != "" and re.sub(r"\W+", "", tmp_str):
                        text_list.append(
                            {"tag": "narration", "text": tmp_str})
                    tmp_str = i
                    flag = 1
                    continue
            tmp_str += i
        if tmp_str != "" and re.sub(r"\W+", "", tmp_str):
            text_list.append({"tag": "narration", "text": tmp_str})

        if self.tags_data is None or 'dialogue' not in self.tags_data or not text_list:
            return text_list

        # todo: 不知道干嘛用，等后面再说
        if not self.tags_data['dialogue'].get("role") and not self.tags_data['dialogue'].get("'defaultRole'"):
            return text_list

        text_structure = ""
        narration_total = 0
        dialogue_total = 0
        narration_text = ""
        for i in range(len(text_list)):
            if text_list[i]['tag'] == "dialogue":
                text_structure += "d"
                dialogue_total += 1
            else:
                text_structure += "n"
                narration_total += 1
                narration_text = text_list[i]['text']
        if "d" != text_structure:
            his_tts_id = 0
        if "nd" == text_structure:
            his_tts_id = -1

        if narration_total > 0 and dialogue_total > 0:
            roles = self.tags_data['dialogue'].get('role', [])
            # todo:
            if 3 > self.appendRoleMethod > 0:
                roles = self.tmp_role_list
            # 旁白在前，旁白在后
            fRegexs = self.tags_data['dialogue'].get('fRegex', '')
            bRegexs = self.tags_data['dialogue'].get('bRegex', '')
            allroleStr = ""
            if self.useAllRole:
                allroleStr = self.get_all_role_str(roles)
            tmp_tts_id = -1
            tmp_tts_two_id = -1
            if narration_total == 1:
                # 定义 preTextFlag 是否旁白在前 的变量为 False
                pre_text_flag = False
                # 如果 text_structure 第1个字符为 'n'
                if text_structure[0] == "n":
                    # 则 preTextFlag 等于 True
                    pre_text_flag = True

                tmp_tts_id = self.match_role(pre_text_flag, narration_text, roles, allroleStr, fRegexs, bRegexs)

                # 如果没有获取到真正的 tmpTtsID ，则执行
                if tmp_tts_id == -1:
                    # 反向 preTextFlag 是否旁白在前 变量，获取 tmpTtsID
                    tmp_tts_id = self.match_role(not pre_text_flag, narration_text, roles, allroleStr, fRegexs,
                                                 bRegexs)

                # 如果正确获取到 tmpTtsID 的值，则执行
                if tmp_tts_id != -1:
                    # 运行 set_voice_id 方法，把 tmpTtsID 添加或修改 list 中 tag = 'dialogue' 的 id 值
                    self.set_voice_id(text_list, tmp_tts_id)
                elif self.default_tts_id != -1:
                    # 否则使用默认对话ID defaultTtsID
                    self.set_voice_id(text_list, self.default_tts_id)

                # 根据 tmpTtsID 的状态再次操作
                if tmp_tts_id != -1:
                    self.set_voice_id(text_list, tmp_tts_id)
                    if self.hisTtsId == -1:
                        # 如果 DiaRule = 默认对话，则留空
                        if self.DiaRule == 0:
                            pass
                        elif self.DiaRule == 1:
                            self.hisTtsId = tmp_tts_id
                else:
                    self.set_voice_id(text_list, self.default_tts_id)
                    if self.hisTtsId == -1:
                        self.hisTtsId = self.default_tts_id
            elif text_structure == "ndn":  # 如果获取到的文本结构为 旁白、对话、旁白，则执行以下代码
                tmp_tts_id = self.match_role(True, text_list[0].get("text"), roles, allroleStr, fRegexs, bRegexs)
                # 如果第一次的旁白文本获取 tmp_tts_id 不成功，则使用旁白在后及第二次旁白文本获取 tmp_tts_id
                if tmp_tts_id == -1:
                    tmp_tts_id = self.match_role(False, text_list[2].get("text"), roles, allroleStr, fRegexs, bRegexs)

                # 如果正确获取到 tmp_tts_id ，做执行
                if tmp_tts_id != -1:
                    # 修改 list 对话ID为 tmp_tts_id
                    text_list[1]['id'] = tmp_tts_id
                elif self.default_tts_id != -1:
                    # 否则修改 list 对话 ID 为默认对话  self.default_tts_id
                    text_list[1]['id'] = self.default_tts_id
            elif text_structure == "ndnd":  # 如果获取到的文本结构为 旁白、对话、旁白、对话，则执行以下代码
                tmp_tts_id = self.match_role(True, text_list[0]["text"], roles, allroleStr, fRegexs, bRegexs)
                # 尝试使用旁白在前及第二次的旁白文本获取 tmp_tts_id
                tmp_tts_two_id = self.match_role(True, text_list[2]["text"], roles, allroleStr, fRegexs, bRegexs)

                # 如果正确获取到 tmp_tts_id ，修改 list[1] 的 id
                if tmp_tts_id != -1:
                    text_list[1]["id"] = tmp_tts_id
                # 否则如果正确获取到 tmp_tts_two_id ，修改 list[1] 的 id
                elif tmp_tts_two_id != -1:
                    text_list[1]["id"] = tmp_tts_two_id
                # 再否则使用默认对话ID
                elif self.default_tts_id != -1:
                    text_list[1]["id"] = self.default_tts_id

                # 如果正确获取到 tmp_tts_two_id ，修改 list[3] 的 id
                if tmp_tts_two_id != -1:
                    text_list[3]["id"] = tmp_tts_two_id
                # 否则如果正确获取到 tmp_tts_id ，修改 list[3] 的 id
                elif tmp_tts_id != -1:
                    text_list[3]["id"] = tmp_tts_id
                # 再否则使用默认对话ID
                elif self.default_tts_id != -1:
                    text_list[3]["id"] = self.default_tts_id
            elif text_structure == "dndn":  # 如果获取到的文本结构为 对话、旁白、对话、旁白，则执行以下代码
                # 尝试使用旁白在后及第一次的旁白文本获取 tmpTtsID
                tmp_tts_id = self.match_role(False, text_list[1]["text"], roles, allroleStr, fRegexs, bRegexs)
                # 尝试使用旁白在后及第二次的旁白文本获取 tmpTtsTwoID
                tmp_tts_two_id = self.match_role(False, text_list[3]["text"], roles, allroleStr, fRegexs, bRegexs)

                # 如果正确获取到 tmpTtsID ，做执行
                if tmp_tts_id != -1:
                    # 修改 list 对话ID为 tmpTtsID
                    text_list[0]["id"] = tmp_tts_id
                elif tmp_tts_two_id != -1:
                    # 否则修改 list 对话 ID 为默认对话 tmpTtsTwoID
                    text_list[0]["id"] = tmp_tts_two_id
                elif self.default_tts_id != -1:
                    # 否则修改 list 对话 ID 为默认对话 defaultTtsID
                    text_list[0]["id"] = self.default_tts_id

                # 如果正确获取到 tmpTtsTwoID ，做执行
                if tmp_tts_two_id != -1:
                    # 修改 list 对话ID为 tmpTtsTwoID
                    text_list[2]["id"] = tmp_tts_two_id
                elif tmp_tts_id != -1:
                    # 否则修改 list 对话 ID 为默认对话 tmpTtsID
                    text_list[2]["id"] = tmp_tts_id
                elif self.default_tts_id != -1:
                    # 否则修改 list 对话 ID 为默认对话 defaultTtsID
                    text_list[2]["id"] = self.default_tts_id
            else:  # 如果超出以上 textStructure 状态，测试时可能ID会显示异常
                if self.DiaRule == 0 or self.DiaRule == 2:
                    # 默认对话
                    if self.default_tts_id != -1:
                        for item in text_list:
                            item['id'] = self.default_tts_id

                elif self.DiaRule == 1:
                    for i, item in enumerate(text_list):
                        if item.get('tag') == "dialogue":
                            closestNarration = self.get_closest_narration(text_list, i)
                            if closestNarration is not None:
                                preTextFlag = i > closestNarration['index']
                                tmpTtsID = self.match_role(preTextFlag, closestNarration['content'], roles, allroleStr,
                                                           fRegexs, bRegexs)
                                if tmpTtsID != -1:
                                    item['id'] = tmpTtsID
                                elif self.default_tts_id != -1:
                                    item['id'] = self.default_tts_id
                            else:
                                # 默认对话
                                if self.default_tts_id != -1:
                                    for item in text_list:
                                        item['id'] = self.default_tts_id
                                break

                    # 所有无法识别的对话, 使用所有配置随机，留空就好， 程序本身功能
                elif self.DiaRule == 3:
                    pass  # 实现随机分配或其他处理逻辑

        elif dialogue_total > 0:
            # todo: 只有对话
            # 默认对话
            if self.DiaRule == 0:
                if self.default_tts_id != -1:
                    self.set_voice_id(text_list, self.default_tts_id)

            # 最后一次对话
            elif self.DiaRule == 1:
                if self.hisTtsId > 0:
                    self.set_voice_id(text_list, self.hisTtsId)
                else:
                    if self.default_tts_id != -1:
                        self.set_voice_id(text_list, self.default_tts_id)
            # 倒数第二次对话
            elif self.DiaRule == 2:
                DialogueID = self.default_dialogue_id()  # 假设这是defaultDialogueID方法的Python实现
                # print("\n默认对话ID判断结果：")
                # print(DialogueID)

                if self.randomOrInOrder == 1:
                    if len(self.historicalDialogueIdList) > 1 and self.historicalDialogueIdList[-1] != \
                            self.historicalDialogueIdList[
                                -2]:
                        self.set_voice_id(text_list, self.historicalDialogueIdList[-2])
                    else:
                        if self.default_tts_id != -1:
                            self.set_voice_id(text_list, self.default_tts_id)

                elif self.randomOrInOrder == 2:
                    if len(self.historicalDialogueIdList) <= 1:
                        if self.default_tts_id != -1:
                            self.set_voice_id(text_list, self.default_tts_id)
                    elif len(self.historicalDialogueIdList) == 2:
                        if DialogueID == 3:
                            if self.default_tts_id != -1:
                                self.set_voice_id(text_list, self.default_tts_id)
                        else:
                            if self.historicalDialogueIdList[-1] == self.historicalDialogueIdList[-2]:
                                if self.default_tts_id != -1:
                                    self.set_voice_id(text_list, self.default_tts_id)
                            else:
                                self.set_voice_id(text_list, self.historicalDialogueIdList[-2])
                    elif len(self.historicalDialogueIdList) > 2:
                        if DialogueID in (8, 3):
                            if self.default_tts_id != -1:
                                self.set_voice_id(text_list, self.default_tts_id)
                        else:
                            if self.historicalDialogueIdList[-1] == self.historicalDialogueIdList[-2]:
                                self.set_voice_id(text_list, self.historicalDialogueIdList[-3])
                            else:
                                self.set_voice_id(text_list, self.historicalDialogueIdList[-2])

            # 所有无法识别的对话,使用所有配置随机，留空就好
            elif self.DiaRule == 3:
                pass  # 根据需求可能需要添加处理逻辑

        # 假设的日志输出
        return text_list

    def get_all_role_str(self, roles):
        # 取用|分隔的全部角色名
        allrole = []
        for role_idx, role in enumerate(roles):
            # 如果没有roles[role_idx]属性或者roles[role_idx].value属性为空，则退出循环
            if not role.get("value"): continue
            # logger.debug(role)

            # 去除role['value']值里面的换行符
            tmp_role_value = regex.sub(r'\n', '', role.get("value"))

            # 如果tmp_role_value值为空，则退出循环
            if not tmp_role_value:
                continue

            # 以 | 分隔的文本转为数组
            tmp_roles = tmp_role_value.split('|')
            for tmp_role in tmp_roles:
                # 如果allrole列表中没有tmp_role这个值，则把这个值添加到allrole列表的最后位置
                if tmp_role not in allrole:
                    allrole.append(tmp_role)

        # 返回allrole列表以 | 分隔转文本的值
        return '|'.join(allrole)


if __name__ == '__main__':
    novel = "G:\\temp\\AI\\文本演示\\多角色识别.txt"
    # novel = "G:\\temp\\AI听书本地一键包\\文本演示\\Chapter_3.txt"
    tags_data = {'dialogue': {'defaultRole': [{'id': 'AzureCN', 'value': 'dialogue'}, {'id': '云杰', 'value': 'boy'},
                                              {'id': '晓晓 多语言', 'value': 'youngadultfemale'},
                                              {'id': '云皓', 'value': 'actorprotagonist'},
                                              {'id': '云野', 'value': 'seniormale'},
                                              {'id': '云枫', 'value': 'youngadultmale'},
                                              {'id': '云健', 'value': 'olderadultmale'},
                                              {'id': '晓悠', 'value': 'girl'}, {'id': '晓颜', 'value': 'seniorfemale'},
                                              {'id': '晓萱', 'value': 'olderadultfemale'}],
                              'defaultFlag': [{'id': 'AzureCN', 'value': True}, {'id': '云杰', 'value': False},
                                              {'id': '晓晓 多语言', 'value': False}, {'id': '云皓', 'value': False},
                                              {'id': '云野', 'value': False}, {'id': '云枫', 'value': False},
                                              {'id': '云健', 'value': False}, {'id': '晓悠', 'value': False},
                                              {'id': '晓颜', 'value': False}, {'id': '晓萱', 'value': False}],
                              'role': [{'id': '云杰', 'value': '墨少杰'}, {'id': '晓晓 多语言', 'value': ''},
                                       {'id': '云皓', 'value': '我'}, {'id': '云野', 'value': ''},
                                       {'id': '云枫', 'value': '二叔'}, {'id': '云健', 'value': ''},
                                       {'id': '晓悠', 'value': ''}, {'id': '晓颜', 'value': ''},
                                       {'id': '晓萱', 'value': ''}]}, 'narration': {}}
    # print(CharacterRecognition().handle_text(text, self.tags_data))
    t = []
    c = CharacterRecognition(tags_data)
    # c.append_rule()
    s = '“气”，人一旦沾染，就会“畸变”,"懂了么？"。'
    print(c.handle_text(s))
    # with open(novel, 'r', encoding='utf-8') as f:
    #     for i in f.readlines():
    #         if i.strip() == '':
    #             continue
    #         t.append(c.handle_text(i))
    # for t1 in t:
    #     for i in t1:
    #         if regex.sub("\W+", '', i['text']):
    #             print(i)
    #             # print(f'{i["tag"]} \t {i.get("id")} \t\t {i["text"].strip()}')

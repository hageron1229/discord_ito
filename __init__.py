import random
import pprint
import asyncio
import discord
import csv

async def Ito_init(message,client):
	t = Ito(message,client,True)
	await t.hello()
	await t.init()
	return t

class Ito:
	def __init__(self,message,client,boo=False):
		if boo==False:
			raise Exception("直接の初期化は禁止されています。")
		self.init_user = message.author
		self.channel = message.channel
		self.client = client
		self.guild = message.channel.guild
		self.member =[]
		self.message = {}
		self.emoji = {
			"play":"\U000025B6",
			"stop":"\U000026D4",
			"maru":"\U00002B55",
			"batsu":"\U0000274C",
			"add":"\U000023EB",
			"back":"\U000023EC",
			"raise_hand":"\U0000270B",
			"next":"\U000023E9",
			"up":"⬆️",
			"down":"⬇️",
			#"plus":"➕",
			"plus":"🔼",
			#"minus":"➖",
			"minus":"🔽",
			"angel":"😇",
			"dice":"🎲",
			"joker":"🃏",
		}
		self.settings = {
			"range_min":1,
			"range_max":100,
			"life":3,
			"adult":True,
		}
		self.theme = {"normal":[],"adult":[]}
		with open("functions/ito/theme.csv",mode="r",encoding="utf-8") as f:
			reader = csv.reader(f)
			for row in reader:
				txt,ty = row
				self.theme[ty].append(txt)
		self.level = 1


	async def del_(self):
		pass

	async def hello(self):
		#await self.send("itoを開始します。")
		await self.reload_main()

	async def init(self):
		pass

	async def reload_main(self):
		if self.member:
			member_message = "・"+"\n・".join([m.display_name for m in self.member])
		else:
			member_message = "-"
		settings_txt = f"・数字の範囲 : [{self.settings['range_min']},{self.settings['range_max']}]"
		fields = [[f"[参加者一覧]",member_message],[f"[レベル{self.level}]",f"ひとり{self.level}枚"],["[設定]",settings_txt]]
		embed=self.create_embed("ito online","",fields,discord.Colour.green())
		embed.set_thumbnail(url="https://m.media-amazon.com/images/I/71lTZzCnvRL._AC_SL1500_.jpg")
		if "main" in self.message:
			await self.message["main"].edit(embed=embed)
		else:
			self.message["main"] = await self.send(embed=embed)
			await self.message["main"].add_reaction(self.emoji["dice"])
			await self.message["main"].add_reaction(self.emoji["next"])

	def create_embed(self,title,description,fields,color=discord.Colour.green(),inline=False):
		embed = discord.Embed(title=title,description=description,color=color)
		for name,value in fields:
			embed.add_field(name=name,value=value,inline=inline)
		return embed

	async def receve_text(self,message):
		cmd = ".ito"
		if message.content.startswith(cmd+" "):
			txt = message.content[len(cmd+" "):]
			if txt=="start":
				await self.game_start()
			elif txt=="reset":
				self.level = 1
				await self.reload_main()
			elif txt.startswith("settings"):
				arg = txt.split()[1:]
				if len(arg)==2:
					if arg[0]=="range_min":
						self.settings["range_min"] = int(arg[1])
					elif arg[0]=="range_max":
						self.settings["range_max"] = int(arg[1])
					await self.reload_main()
			await message.delete()
		else:
			txt = message.content

	async def receve_reaction(self,reaction,user):
		if reaction.emoji==self.emoji["dice"]:
			if user.id not in [m.id for m in self.member]:
				m = await self.guild.fetch_member(user.id)
				self.member.append(m)
			await self.reload_main()
		elif reaction.emoji==self.emoji["joker"]:
			if user.id in self.id_num:
				#await self.send(user.display_name+"が"+str(self.id_num[user.id])+"を出しました")
				if self.max_value<self.id_num[user.id][0]:
					self.history += f"{self.id_num[user.id][0]} : {user.display_name}\n"
					embed=self.create_embed("場のカード","",[[f"現在の数字 : {self.id_num[user.id][0]}",user.display_name],["履歴",self.history]],discord.Colour.green())
					await self.message["field"].edit(embed=embed)
					#print(self.max_value,end=" → ")
					self.max_value = self.id_num[user.id][0]
					#print(self.max_value)
					del self.id_num[user.id][0]
					if len(self.id_num[user.id])==0:
						del self.id_num[user.id]
					else:
						await reaction.remove(user)
					if len(self.id_num)==0:
						self.level+=1
						self.message["result"] = await self.send(f"成功！\n次はレベル{self.level}です")
						await self.reload_main()
				else:
					#self.history += "\n".join([f"{self.id_num[m.id]} : {m.display_name}\n" for m in self.game_member if m.id in self.id_num])
					self.history += "".join(["".join([f"{item} : {m.display_name}\n" for item in self.id_num[m.id]]) for m in self.game_member if m.id in self.id_num])
					embed=self.create_embed("場のカード","",[[f"現在の数字 : {self.id_num[user.id][0]}",user.display_name],["全カード",self.history]],discord.Colour.green())
					await self.message["field"].edit(embed=embed)
					self.id_num = []
					self.game_member = []
					self.message["result"] = await self.send(f"失敗！\nレベル{self.level}まで達成しました")
					self.level = 1
					await self.reload_main()
		elif reaction.emoji==self.emoji["next"]:
			await self.game_start()
			await reaction.remove(user)

	async def remove_reaction(self,reaction,user):
		if reaction.emoji==self.emoji["dice"]:
			for i in range(len(self.member)):
				if self.member[i].id==user.id:
					del self.member[i]
					break
			await self.reload_main()

	async def send(self,content=False,embed=False,update=True):
		params = {}
		if content:
			params["content"] = content
		if embed:
			params["embed"] = embed
		r = await self.channel.send(**params)
		if update:
			self.latest_message = r
		return r

	async def game_start(self):
		#すでにあるメッセージの削除
		for label in self.message:
			if label=="main": continue
			try:
				await self.message[label].delete()
			except:
				pass
		self.max_value = self.settings["range_min"]-1
		self.game_member = [m for m in self.member]
		self.id_num = {}
		range_max = max(self.settings["range_max"],self.level*len(self.game_member)+self.settings["range_min"]-1)
		cards = random.sample(list(range(self.settings["range_min"],range_max+1)),len(self.game_member)*self.level)
		for i in range(len(self.game_member)):
			c = sorted(cards[i*self.level:(i+1)*self.level])
			txt = "\n".join([f"あなたのカードの数字 : "+str(j) for j in c])
			self.message[str(self.game_member[i].id)] = await self.game_member[i].send(txt)
			self.id_num[self.game_member[i].id] = c

		embed=self.create_embed("お題",f"**{self.get_theme()}**",[],discord.Colour.red())
		self.message["theme"] = await self.send(embed=embed)

		#場のカード
		self.history = ""
		embed=self.create_embed("場のカード","",[["現在の数字 : -","-"],["履歴","-"]],discord.Colour.green())
		self.message["field"] = await self.send(embed=embed)
		await self.message["field"].add_reaction(self.emoji["joker"])

	def get_theme(self):
		if self.settings["adult"]:
			return random.choice(self.theme["adult"]+self.theme["normal"])
		else:
			return random.choice(self.theme["normal"])



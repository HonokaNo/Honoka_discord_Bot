import discord
from discord.ext import commands
from discord.ext.commands import errors
import time
import threading
import subprocess
import ffmpeg
import re
from datetime import datetime
import random
import os
import sys
import urllib.parse

client = commands.Bot(command_prefix='*', help_command=None)
voice_client = None

alerms = []
msgchannels = []
msgs = []
mentions = []
whomentions = []

uses = [False, False, False]

whomsg = False
nowChannel = None

#if not discord.opus.is_loaded():
#	print("client opus is_loaded -------------------------------------")
#	discord.opus.load_opus("heroku-buildpack-libopus")

@client.command()
async def hello(channel):
	await channel.send('Hello!')
	await channel.send('Hello2!')

@client.command()
async def karaoke(channel, *, arg):
	# urllib.parse.quoteを使うと簡単にエンコーディングできる
	utf8_url = urllib.parse.quote(arg, encoding='utf-8')
	sjis_url = urllib.parse.quote(arg, encoding='shift-jis')
	await channel.send('https://www.joysound.com/web/search/cross?match=1&keyword=' + utf8_url)
	await channel.send('https://www.clubdam.com/karaokesearch/?keyword=' + utf8_url)
	await channel.send('http://karatetsu.jp/sp/mlist_smode=search&keyword=' + sjis_url + '.html')
	await channel.send('http://karatetsu.jp/sp/alist_smode=search&keyword=' + sjis_url + '.html')

@karaoke.error
async def karaoke_error(channel, error):
	if isinstance(error, errors.MissingRequiredArgument):
		await channel.send("help: *karaoke song/artist")

@client.command()
async def movie(channel):
	if len(channel.message.attachments) >= 1:
		print(channel.message.attachments[0].filename)
		fname = channel.message.attachments[0].filename
		if fname.endswith(".mp3") or fname.endswith(".m4a") or fname.endswith(".wav"):
			await channel.message.attachments[0].save(fname)
			print("ffmpeg -loop 1 -r 30000/1000 -input black.png -i " + fname + " -vcodec libx264 -shortest -fs 25MB " + fname + ".mp4")
			subprocess.run("ffmpeg -loop 1 -r 30000/1000 -i black.png -i " + fname + " -vcodec libx264 -acodec aac -strict experimental -ab 320k -ac 2 -ar 44100 -pix_fmt yuv420p -shortest -crf 300 -fs 7MB -threads 16 " + fname + ".mp4")
			subprocess.run("ffmpeg -i " + fname + ".mp4 -threads 16 " + fname + ".webm")
			await channel.send(file=discord.File("./" + fname + ".webm"))
			os.remove(fname)
			os.remove(fname + ".mp4")
			os.remove(fname + ".webm")
		else:
			await channel.send("this file is not supported!")
	else:
		await channel.send("argument(audio file) is missing!")

@client.command()
async def help(channel):
	await channel.send("Python Bot Help")
	await channel.send("*karaoke value      曲/歌手名を検索します")
	await channel.send("example:*karaoke ABC    ABCという曲/歌手で検索")
	await channel.send("*alerm time [msg] [ismention(True/False)]    time秒後にアラームを発信します")
	await channel.send("*alerm 10    10秒後にアラームを発信")
	await channel.send("*alerm 10 \"Success! ful\"    10秒後にSuccess! fulとアラームを発信")
	await channel.send("*alerm 10 Success! True    10秒後にSuccess!とメンション付きでアラームを発信")
	await channel.send("*alermのメッセージは1単語しかできないので注意")
	await channel.send("*join    ボイスチャンネルに参加させます。チャット欄のメッセージ/DMのメッセージを読み上げます")
	await channel.send("*leave    ボイスチャンネルから抜けまーす")
	await channel.send("*ping    テキスト送信のpingを計測します")
	await channel.send("*warikan price num    割り勘のときの金額を計算します")
	await channel.send("*readname True/False    メッセージ読み上げ時に名前を読み上げます")
	await channel.send("*setchannel True/False    メッセージを読み上げるチャンネルを固定します")
	await channel.send("*hayakuchi    早口言葉に挑戦します!(毎回成功しちゃうけどね☆")

@client.command()
async def alerm(channel, *args):
	if len(args) == 0:
		await channel.send("help: *alerm time [msg] [ismention(True/False)]")
		return
	if len(args) > 3:
		await channel.send("help: *alerm time [msg] [ismention(True/False)]")

	time = 0
	msg = "Alerm!"
	ismention = False
	whomention = None
	_mention = channel.author

	if len(args) >= 1:
		time = int(args[0])
	if len(args) >= 2:
		msg = args[1]
	if len(args) == 3:
		ismention = bool(args[2])

	alerms.append(time)
	msgchannels.append(channel)
	msgs.append(msg)
	mentions.append(ismention)
	whomentions.append(_mention)

@client.command()
async def join(ctx):
	vc = ctx.author.voice.channel
	await vc.connect()

@client.command()
async def leave(ctx):
	await ctx.voice_client.disconnect()

@client.command()
async def ping(channel):
	current = datetime.utcnow()
	await channel.send("pinging...")
	current0 = datetime.utcnow()

	pinged = current0 - current
	await channel.send("ping success!")
	await channel.send("sec:" + str(pinged.seconds) + " microsec:" + str(pinged.microseconds))

@client.command()
async def warikan(channel, price, num):
	price_i = int(price)
	num_i = int(num)
	ones = int(price_i / num_i)
	div = price_i % num_i

	await channel.send(str(num_i) + " 人で " + str(price_i) + " 円を割り勘するんだよ！")
	await channel.send("一人 " + str(ones) + " 円だよ!")
	if div != 0:
		await channel.send(str(div) + " 円 余りが出ちゃったよ!")

@client.command()
async def readname(channel, arg):
	global whomsg
	whomsg = bool(arg)
	await channel.send("名前読み上げ設定を " + str(whomsg) + " に設定しました")

@client.command()
async def setchannel(channel, arg):
	set = bool(arg)
	if set == False:
		nowChannel = None
	else:
		nowChannel = channel
	await channel.send("チャンネル固定を " + str(set) + " に設定しました")

@client.command()
async def hayakuchi(channel):
	hayakuchi_repertory = ["隣の客はよく柿食う客だ", "東京特許許可局", "赤巻紙青巻紙黄巻紙"]
	r = random.randint(0, len(hayakuchi_repertory))
	msg = ""

	await channel.send("早口言葉いうね!")

	# リストにレパートリーを格納してランダムに生成したインデックスにアクセス
	msg = hayakuchi_repertory[r]
	await channel.send(msg)

	creat_WAV(msg, "normal", "1.5")
	source = discord.FFmpegPCMAudio("output.wav")
	channel.voice_client.play(source)

@client.command()
async def reload(channel):
	# Devの私のID決め打ちです
	if channel.message.author.id == 473041372367290371 or channel.message.author.id == 779695802062602271:
		await channel.send("reloading...")
		print(sys.argv)
		print(sys.executable)
		print(__file__)
		os.execl(sys.executable, __file__)
		exit(0)
	else:
		await channel.send("何をやろうとしているのかね?")
		await channel.send(f"{channel.message.author.mention}さん?")

def creat_WAV(input, voice_type, speed):
	with open("input.txt", "w", encoding="sjis") as file:
		file.write(input)

	command = "C:/open_jtalk/bin/open_jtalk -m {m} -x {x} -r {r} -ow output.wav input.txt"

	x = "C:/open_jtalk/bin/dic"
	m = "C:/open_jtalk/bin/mei/mei_" + voice_type + ".htsvoice"
	r = speed

	args = {"x":x, "m":m, "r":r}
	cmd = command.format(**args)

	subprocess.run(cmd)

@client.event
async def on_message(message):
	global whomsg

	if message.content.startswith(client.command_prefix):
		pass
	elif message.author == client.user:
		pass
	elif message.guild.voice_client:
		# 読み上げチャンネルを固定している
		# かつ指定したチャンネルではない
		if nowChannel != None and nowChannel != message.channel:
			pass

		name = message.author.nick
		if name == None:
			name = message.author.name

		if "http" in message.content:
			message.content = "リンクがあるよ!めんどくさいから読まなくていいよね!"

		msg = message.content.replace("\n", " ")
		if "悲し" in message.content or "しょぼん" in message.content or "´・ω・" in message.content:
			feeling = "sad"
		elif "楽し" in message.content or "わーい" in message.content:
			feeling = "happy"
		elif "怒" in message.content or "ぷんぷん" in message.content or "プンプン" in message.content:
			feeling = "angry"
		elif "恥ず" in message.content or "はずかしい" in message.content:
			feeling = "bashful"
		else:
			feeling = "normal"

		if whomsg:
			msg = name + " さん " + msg
		# create_WAV部分は共通なのでまとめる
		creat_WAV(msg, feeling, "1.0")
		source = discord.FFmpegPCMAudio("output.wav")
		message.guild.voice_client.play(source)
	else:
		pass

	await client.process_commands(message)

def timer():
	while True:
		index = 0
		for t in alerms:
			alerms[index] -= 1
			if alerms[index] == 0:
				if mentions[index]:
					client.loop.create_task(msgchannels[index].send(whomentions[index].mention + " " + msgs[index]))
				else:
					client.loop.create_task(msgchannels[index].send(msgs[index]))
				del alerms[index]
				del msgchannels[index]
				del msgs[index]
				del mentions[index]
			index += 1
		time.sleep(1)

t1 = threading.Thread(target=timer)
t1.setDaemon(True)
t1.start()

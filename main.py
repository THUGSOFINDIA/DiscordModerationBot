import discord,json,os,re,httplib2,time,datetime
from apiclient import discovery
from google.oauth2 import service_account

client = discord.Client()

with open("Config/token.json") as token_file:
    tokens = json.load(token_file)
    
with open("Config/config.json") as config_file:
    config = json.load(config_file);

with open("Config/help.json") as help_file:
    helpdata = json.load(help_file)

prefix = config["prefix"]

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
secret_file = "Config/client_secret.json"
credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
service = discovery.build('sheets','v4',credentials=credentials)
    
warninglogid = tokens["warninglogid"]
verifylogid = tokens["verifylogid"]

def get_warnings():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Warnings!A2:H", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def get_kicks():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Kicks!A2:G", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]

def get_bans():
    global warninglogid
    response = service.spreadsheets().values().get(spreadsheetId = warninglogid, range = "Bans!A2:G", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute()
    return response["values"]
    
warnings = get_warnings()
kicks = get_kicks()
bans = get_bans()

@client.event
async def on_ready():
    global warnings
    warnings = get_warnings()
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global warnings
    global kicks
    global bans
    global warninglogid
    global verifylogid
    global prefix
    global helpdata
    if message.author == client.user:
        return
    if not (message.content.startswith(prefix)):
        return
    args = (message.content[1:]).split(" ")
    if len(args) == 0:
        return
    command = args.pop(0)
    #perms means the permission the user has: developer -> 40, has admin rights (ie csuite+ and admin+) -> 31, moderator -> 30, Other HRs -> 20, verified members -> 11, message sent in DM -> 10, all users -> 0
    perms = 0
    if message.author.id in [156390113654341632,463016897110343690,676596209627955231]: 
        perms = 40 
    elif isinstance(message.channel, discord.abc.GuildChannel):
        if message.author.guild_permissions.administrator:
            perms = 31
        else:
            for role in message.author.roles:
                if role.id == 348722815903596545 and perms < 30:
                    perms = 30
                if role.id == 436418888704720896 and perms < 20:
                    perms = 20
                if role.id == 359604396276973570 and perms < 11:
                    perms = 11
    else:
        perms = 10
    if (command == "help" and perms >= 0):
        targetcmd = ""
        if len(args) == 0:
            targetcmd = "all"
        else:
            targetcmd = args[0]
        if targetcmd.startswith("!"):
            targetcmd = targetcmd[1:]
        if targetcmd.startswith(prefix):
            targetcmd = targetcmd[1:]
        output = ""
        if targetcmd == "all":
            for cmd,data in helpdata.items():
                if data["perms"] <= perms:
                    output += "`{0}{1} {2}`- {3}\n".format(prefix,cmd,data["usage"],data["description"])
            await message.channel.send(output+"Note that arguments encased in angle brackets (`<>`) are mandatory, while those encased in square brackets (`[]`) are optional.")
            return
        elif targetcmd in helpdata:
            data = helpdata[targetcmd]
            if data["perms"] <= perms:
                await message.channel.send("`{0}{1} {2}`- {3}\n Note that arguments encased in angle brackets (`<>`) are mandatory, while those encased in square brackets (`[]`) are optional.".format(prefix,targetcmd,data["usage"],data["description"]))
                return
            else:
                await message.channel.send("You cannot access the help for this command.")
                return
        else:
            await message.channel.send("The command {}{} is not a command.".format(prefix,targetcmd))
            return
    if (command == "getsource" and perms >= 0):
        await message.channel.send("This bot is open source, the source code is at: <https://github.com/RandomGamer123/DiscordModerationBot>.")
        return
    if (command == "testsheets" and perms >= 30):
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "TestSheet!A1:B2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[["testing",message.id]]}).execute()
    if (command == "print" and perms >= 40):
        print(" ".join(args))
    if (command == "warn" and perms >= 30):
        warnings = get_warnings()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0].isnumeric()):
            id = args[0]
        else:
            pingmatch = re.compile("<@![0-9]{6,19}>");
            if pingmatch.match(args[0]):
                id = args[0][3:-1]
            else:
                await message.channel.send("Argument 1 of this command must be a user id or mention.")
                return
        user = client.get_user(int(id))
        username = user.name+" #"+user.discriminator
        mod = message.author.name
        uniqueid = "W"+str(len(warnings)+1)
        args.pop(0)
        reason = " ".join(args)
        embed = discord.Embed(colour=discord.Colour(0xf0f05d), timestamp=datetime.datetime.utcfromtimestamp(time.time()))
        embed.set_footer(text="Case "+uniqueid)
        if message.guild:
            if message.guild.id == 295823905120190465:
                embed.add_field(name="**Notice of Warning**", value=reason)
            else: 
                embed.add_field(name="**Notice of Warning**", value="You have been warned in SWISS International Air Lines' Discord for reason: \n"+reason)
        else:
            embed.add_field(name="**Notice of Warning**", value="You have been warned in SWISS International Air Lines' Discord for reason: \n"+reason)
        try:
            await user.send(embed=embed)
        except:
            await message.channel.send("The bot cannot DM that user, no DM notification has been sent. The user will still be warned.")
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Warnings!A1:H2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[str(user.id),username,uniqueid,"",reason,(mod+" (Warned via bot)"),str(round(time.time())),"Active"]]}).execute()
        await message.channel.send("User <@!"+str(user.id)+"> has been warned for reason: `"+reason+"` by moderator "+mod)
        warnings = get_warnings()
    if (command == "removewarning" and perms >=30):
        warnings = get_warnings()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if args[0].startswith("W"):
            case = ""
            row = 1
            rept = 1
            for warning in warnings:
                if case == "":
                    row = row + 1
                    if warning[2] == args[0]:
                        case = warning
                if warning[2].startswith("R"):
                    if ((warning[2].split("-",1))[0])[1:] == args[0][1:]:
                        rept = rept + 1
            if case == "":
                await message.channel.send("Warning with case number "+args[0]+" cannot be found.")
                return
            if case[7] == "Removed":
                await message.channel.send("This warning has already been removed. To reinstate this warning, please use the {}editwarning command.".format(prefix))
                return
            uniqueid = "R"+(args[0][1:])
            args.pop(0)
            reason = " ".join(args)
            mod = message.author.name
            service.spreadsheets().values().update(spreadsheetId = warninglogid, range = "Warnings!H"+str(row), valueInputOption = "RAW", body = {"values":[["Removed"]]}).execute()
            service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Warnings!A1:H2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[case[0],case[1],uniqueid+"-"+str(rept),"",reason,(mod+" (Warning removed via bot)"),str(round(time.time())),"NA"]]}).execute()
            await message.channel.send("Warning W"+(uniqueid[1:])+" has been marked as removed by "+mod+" for reason:\n"+reason)
        else:
            await message.channel.send("Warning case number must start with W.")
            return
    if (command == "warningssheet" and perms >=30):
        await message.channel.send("Link to warning sheet: <https://docs.google.com/spreadsheets/d/1OM14Up7i-XurecAYqg6JLTxeGoGnabogz-6fE7ffJHI/edit#gid=0> (Ask Random to give you editing permissions.)")
        return
    if (command == "editwarning" and perms >=30):
        await message.channel.send("This command is still WIP, please directly edit the warnings sheet at <https://docs.google.com/spreadsheets/d/1OM14Up7i-XurecAYqg6JLTxeGoGnabogz-6fE7ffJHI/edit#gid=0> instead. (Ask Random to give you editing permissions.)")
        return
    if (command == "warnings" and perms >=30):
        warnings = get_warnings()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0] == "all"):
            msgstring = ""
            for warning in warnings:
                if len(args) < 2:
                    if warning[7] == "Removed":
                        continue
                    if warning[2].startswith("R"):
                        continue
                elif args[1] != "-removed": 
                    if warning[7] == "Removed":
                        continue
                    if warning[2].startswith("R"):
                        continue
                if msgstring != "":
                    msgstring = msgstring+"\n"
                if warning[6] == "NA":
                    evttime = "an unknown time"
                else:
                    evttime = datetime.datetime.fromtimestamp(int(warning[6])).strftime('%Y-%m-%d %H:%M:%S')
                if warning[2].startswith("R"):
                    msgstring = msgstring+"Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has had warning W"+str(warning[2][1:])+" removed by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
                    continue
                if warning[7] == "Removed":
                    msgstring = msgstring+"[WARNING HAS BEEN REMOVED] Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has been warned by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
                    continue 
                msgstring = msgstring+"Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has been warned by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
            for i in range(0,len(msgstring),1994):
                await message.channel.send("```"+msgstring[i:i+1994]+"```")
        else:
            if (args[0].isnumeric()):
                searchid = args[0]
            else:
                pingmatch = re.compile("<@![0-9]{6,19}>");
                if pingmatch.match(args[0]):
                    searchid = args[0][3:-1]
                else:
                    await message.channel.send("Argument 1 of this command must be a user id or mention.")
                    return
            msgstring = ""
            for warning in warnings:
                if len(args) < 2:
                    if warning[7] == "Removed":
                        continue
                    if warning[2].startswith("R"):
                        continue
                elif args[1] != "-removed": 
                    if warning[7] == "Removed":
                        continue
                    if warning[2].startswith("R"):
                        continue
                if str(warning[0]) == str(searchid):
                    if msgstring != "":
                        msgstring = msgstring+"\n"
                    if warning[6] == "NA":
                        evttime = "an unknown time"
                    else:
                        evttime = datetime.datetime.fromtimestamp(int(warning[6])).strftime('%Y-%m-%d %H:%M:%S')
                    if warning[2].startswith("R"):
                        msgstring = msgstring+"Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has had warning W"+str(warning[2][1:])+" removed by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
                        continue
                    if warning[7] == "Removed":
                        msgstring = msgstring+"[WARNING HAS BEEN REMOVED] Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has been warned by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
                        continue 
                    msgstring = msgstring+"Case "+warning[2]+": User "+warning[1]+" ("+warning[0]+") has been warned by "+warning[5]+" at "+evttime+" for reason: \n"+warning[4]
            if (msgstring == ""):
                await message.channel.send("This user has no warnings.")
            else:
                for i in range(0,len(msgstring),1994):
                    await message.channel.send("```"+msgstring[i:i+1994]+"```")
    if (command == "kick" and perms >= 30):
        kicks = get_kicks()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0].isnumeric()):
            id = args[0]
        else:
            pingmatch = re.compile("<@![0-9]{6,19}>");
            if pingmatch.match(args[0]):
                id = args[0][3:-1]
            else:
                await message.channel.send("Argument 1 of this command must be a user id or mention.")
                return
        user = client.get_user(int(id))
        if (user.id == message.author.id):
            await message.channel.send("You cannot kick yourself.")
            return
        username = user.name+" #"+user.discriminator
        mod = message.author.name
        uniqueid = "K"+str(len(kicks)+1)
        args.pop(0)
        reason = " ".join(args)
        embed = discord.Embed(colour=discord.Colour(0xff0000), timestamp=datetime.datetime.utcfromtimestamp(time.time()))
        embed.set_footer(text="Case "+uniqueid)
        if message.guild:
            if message.guild.id == 295823905120190465:
                embed.add_field(name="**Notice of Kicking**", value=reason)
            else: 
                embed.add_field(name="**Notice of Kicking**", value="You have been kicked from SWISS International Air Lines' Discord for reason: \n"+reason+"\n You can rejoin the server using the link: <https://discord.gg/SFr5f6D>.")
        else:
            embed.add_field(name="**Notice of Kicking**", value="You have been kicked from SWISS International Air Lines' Discord for reason: \n"+reason+"\n You can rejoin the server using the link: <https://discord.gg/SFr5f6D>.")
        try:
            await user.send(embed=embed)
        except:
            await message.channel.send("The bot cannot DM that user, no DM notification has been sent. The user will still be kicked.")
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Kicks!A1:G2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[str(user.id),username,uniqueid,"",reason,(mod+" (Kicked via bot)"),str(round(time.time()))]]}).execute()
        await message.guild.kick(user,reason=reason)
        await message.channel.send("User <@!"+str(user.id)+"> has been kicked for reason: `"+reason+"` by moderator "+mod)
        kicks = get_kicks()
    if (command == "ban" and perms >= 30):
        bans = get_bans()
        if len(args) < 1:
            await message.channel.send("You need at least 1 argument in this command.")
            return
        if (args[0].isnumeric()):
            id = args[0]
        else:
            pingmatch = re.compile("<@![0-9]{6,19}>");
            if pingmatch.match(args[0]):
                id = args[0][3:-1]
            else:
                await message.channel.send("Argument 1 of this command must be a user id or mention.")
                return
        user = client.get_user(int(id))
        if (user.id == message.author.id):
            await message.channel.send("You cannot ban yourself.")
            return
        username = user.name+" #"+user.discriminator
        mod = message.author.name
        uniqueid = "B"+str(len(bans)+1)
        args.pop(0)
        reason = " ".join(args)
        embed = discord.Embed(colour=discord.Colour(0xff0000), timestamp=datetime.datetime.utcfromtimestamp(time.time()))
        embed.set_footer(text="Case "+uniqueid)
        if message.guild:
            if message.guild.id == 295823905120190465:
                embed.add_field(name="**Notice of Banning**", value=reason)
            else: 
                embed.add_field(name="**Notice of Banning**", value="You have been banned from SWISS International Air Lines' Discord for reason: \n"+reason)
        else:
            embed.add_field(name="**Notice of Banning**", value="You have been banned from SWISS International Air Lines' Discord for reason: \n"+reason)
        try:
            await user.send(embed=embed)
        except:
            await message.channel.send("The bot cannot DM that user, no DM notification has been sent. The user will still be banned.")
        service.spreadsheets().values().append(spreadsheetId = warninglogid, range = "Bans!A1:G2", valueInputOption = "RAW", insertDataOption = "INSERT_ROWS", body = {"values":[[str(user.id),username,uniqueid,"",reason,(mod+" (Banned via bot)"),str(round(time.time()))]]}).execute()
        await message.guild.ban(user,reason=reason)
        await message.channel.send("User <@!"+str(user.id)+"> has been banned for reason: `"+reason+"` by moderator "+mod)
        bans = get_bans()         
    if (command == "verify" and perms >=0):
        if len(args) == 0:
            await message.channel.send("Verification instructions: Visit <https://www.roblox.com/games/4890252160/SWISS-Verification-Game> to get a verification code valid for 5 minutes. Then input your code and Roblox username in Discord using the command `!verify <code> <username>`. Do not include the brackets.")
            return
        if len(args) < 2:
            await message.channel.send("You need at least 2 arguments for this command. Command format: !verify <code> <username>. Do not include the brackets. Visit <https://www.roblox.com/games/4890252160/SWISS-Verification-Game> to get the verification code.")
            return
        verifycodes = (service.spreadsheets().values().get(spreadsheetId = verifylogid, range = "RobloxCodePairs!A2:F", majorDimension="ROWS", valueRenderOption = "UNFORMATTED_VALUE").execute())["values"]
        code = args.pop(0)
        name = " ".join(args)
        grouprank = -1
        newcodelist = verifycodes[:]
        emptyvals = 0
        boughtclass = "EC"
        rename = ""
        for i in range(len(verifycodes)):
            codepair = verifycodes[i]
            if codepair[3] < time.time():
                newcodelist.remove(codepair)
                emptyvals = emptyvals + 1
            else:
                if codepair[2] == code:
                    if codepair[0] == name:
                        grouprank = codepair[4]
                        boughtclass = codepair[5]
                        emptyvals = emptyvals + 1
                        newcodelist.remove(codepair)
                        rename = codepair[0]
        if (grouprank == -1):
            await message.channel.send("A matching code and username combination cannot be found or your code has expired. Please generate a new code.")
            return
        if isinstance(message.channel, discord.abc.GuildChannel):
            roleguild = message.guild
        else:
            roleguild = client.get_guild(348398590051221505)
        await message.author.edit(nick=rename)
        if (grouprank == 0):
            notingrouprole = discord.utils.get(roleguild.roles, name="NOT IN GROUP")
            if message.guild.id == 348398590051221505:
                verifiedrole = discord.utils.get(roleguild.roles, name="Verified")
                await message.author.remove_roles(verifiedrole)
            await message.author.add_roles(notingrouprole,reason="User is not in the group.")
            await message.channel.send("You are not in the group. Please submit a request to join the group and wait until you are accepted, then request a new code a reverify. The related roles have been given.")
        if (grouprank > 0):
            verifiedrole = discord.utils.get(roleguild.roles, name="Verified")
            passengersrole = discord.utils.get(roleguild.roles, name="Passengers")
            await message.author.add_roles(verifiedrole,reason="User is in the group.")
            await message.author.add_roles(passengersrole,reason="User is in the group.")
            if message.guild.id == 348398590051221505:
                notingrouprole = discord.utils.get(roleguild.roles, name="NOT IN GROUP")
                if grouprank == 241:
                    traineerole = discord.utils.get(roleguild.roles, name="Trainee")
                    await message.author.add_roles(traineerole)
                if grouprank > 242:
                    staffrole = discord.utils.get(roleguild.roles, name="Staff Members")
                    await message.author.add_roles(staffrole)
                    traineerole = discord.utils.get(roleguild.roles, name="Trainee")
                    await message.author.remove_roles(traineerole)
                if boughtclass == "GI":
                    execpass = discord.utils.get(roleguild.roles, name="Executive Passengers")
                    classrole = discord.utils.get(roleguild.roles, name="Gold Investors")
                    await message.author.add_roles(execpass)
                    await message.author.add_roles(classrole)
                if boughtclass == "SI":
                    execpass = discord.utils.get(roleguild.roles, name="Executive Passengers")
                    classrole = discord.utils.get(roleguild.roles, name="Silver Investors")
                    await message.author.add_roles(execpass)
                    await message.author.add_roles(classrole)
                if boughtclass == "FC":
                    execpass = discord.utils.get(roleguild.roles, name="Executive Passengers")
                    classrole = discord.utils.get(roleguild.roles, name="First Class")
                    await message.author.add_roles(execpass)
                    await message.author.add_roles(classrole)
                if boughtclass == "BC":
                    execpass = discord.utils.get(roleguild.roles, name="Executive Passengers")
                    classrole = discord.utils.get(roleguild.roles, name="Business Class")
                    await message.author.add_roles(execpass)
                    await message.author.add_roles(classrole)
                await message.author.remove_roles(notingrouprole)
            await message.channel.send("Verification complete.")
        clearcommand = (service.spreadsheets().values().clear(spreadsheetId = verifylogid, range = "RobloxCodePairs!A2:F")).execute()
        response = (service.spreadsheets().values().update(spreadsheetId = verifylogid, range = "RobloxCodePairs!A2:F", valueInputOption="RAW", body = {"range":"RobloxCodePairs!A2:F","majorDimension":"ROWS","values":newcodelist})).execute()
if os.getenv("BOTTOKEN"):
    bottoken = os.getenv("BOTTOKEN")
else: 
    bottoken = tokens["bottoken"]
client.run(bottoken)
import openai
import discord
import os
import json
from dotenv import load_dotenv
load_dotenv()

model = 'gpt-3.5-turbo'
intents = discord.Intents.all()
client = discord.Client(intents=intents)
permissions = discord.Permissions(8)

openai.organization = os.getenv("ORG")

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.Model.list()

# one token = 4 chars -> round down to 3.5 chars for safety margin
# we use 8k token context so 8192 * 3.5 -> 0.9 * that for the warning limit

sys_prompt_content = 'You are an assistant that communicates only ground truth. You have 160 IQ and are very good at math. You are an AI assistant in my discord server (we talk about technology and AI research)'
sys_prompt = [{"role": "system", "content": sys_prompt_content}]

path = 'conversation_logs'  # replace with your path

# Get a list of all files and directories in the specified directory
files_and_directories = os.listdir(path)

convo_log_count = 0

# Filter out only files (ignore subdirectories)
conversation_logs = [f for f in files_and_directories if os.path.isfile(os.path.join(path, f))]

if conversation_logs:
    print('Using existing conversation logs')
    last_log = conversation_logs[-1]

    for char in last_log:
        try:
            if int(char):
                convo_log_count = int(char)

        except ValueError:
            pass
else:
    context_file = f'conversation_logs_{convo_log_count}.json'
    with open(f'{path}/conversation_logs_{convo_log_count}.json', 'w') as f:
        json.dump(sys_prompt, f, indent=4) 
    print('No logs exist, created one for you')
    
context_file = f'conversation_logs_{convo_log_count}.json'

try:   
    with open('info.json', 'r') as file:
        info = json.load(file)
except:
    info_json_structure = [
    {
        "0": {
            "total_length": 0,
            "summarization": ""
        }
        
    }
]
    with open('info.json', 'w') as file:
        json.dump(info_json_structure, file)
    
# Load the JSON info from a file
with open('info.json', 'r') as file:
    info = json.load(file)


if str(convo_log_count) not in info[0]:
    info[0][str(convo_log_count)] = {
        'total_length': 0,
        'summarization': ''
    }

# Write the updated data back to the file
with open('info.json', 'w') as file:
    json.dump(info, file, indent=4)

# update values
total_ctx_string_len = info[0][str(convo_log_count)]['total_length']   # Replace 100 with the desired value



# Read the current contents of the file, if it exists.
try:
    with open(path + context_file, 'r') as f:
        context = json.load(f)
except FileNotFoundError:
    # If the file doesn't exist, create a new list.
    context = [{"role": "system", "content": 'You are an assistant that communicates only ground truth. You have 160 IQ and are very good at math. You are an AI assistant in my discord server (we talk about technology and AI research)'}]

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


@client.event
async def on_message(message):
    global total_ctx_string_len
    global context_file
    global context
    global convo_log_count
    # get the default text channel of the server
    default_channel = message.channel


    print('something happened')
    if message.content.startswith('/prompt'):
        
        text = message.content[8:]
        if len(text) <= 2000:
            if total_ctx_string_len < 26200: # -> 26200
                if total_ctx_string_len > 23850: # -> 23850
                    # print('Warning: You have used up 90 percent of the max context length for this conversation')
                    await default_channel.send('Warning: You have used up 90 percent of the max context length for this conversation, use `/newchat` to create a new one.')

                with open(f'{path}/conversation_logs_{convo_log_count}.json', 'r') as f:
                    context = json.load(f)
                print(context)
                
                context.append({"role": "user", "content": f"{text}"})

                # send a message to the default channel
                await default_channel.send('Thinking...')
                
            
                 
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=context
                )
                response = response['choices'][0]["message"]['content']
                if len(response) > 2000:
                    await default_channel.send("Discord can't process message longer than 2000 chars.")
                    raise "Discord can't process message longer than 2000 chars."
                    
                
                await default_channel.send(response)   
                context.append({"role": "assistant", "content": response})
                                
                with open(f'{path}/conversation_logs_{convo_log_count}.json', 'w') as f:
                    json.dump(context, f, indent=4)

                total_ctx_string_len += (len(text) + len(response))# plus the openai response
                print(total_ctx_string_len)
                with open('info.json', 'r') as f:
                    info = json.load(f)

                print('temp:', info)
                info[0][str(convo_log_count)]['total_length'] = total_ctx_string_len
                

                with open('info.json', 'w') as f:
                    json.dump(info, f, indent=4)

            else:
                # insert a new conversation func here as well
                await new_conversation(default_channel, True)
        else:
            # print('Too long, please send shorter messages.')
            await default_channel.send('Too long, please send shorter messages.')
            
    elif message.content.startswith('/new'):
        if total_ctx_string_len < 3750:
            # print(f'Total context must be over 50% of the maximum to reset. Current: {100*total_ctx_string_len/7500:.1f}%')
            await default_channel.send(f'Total context must be over 50% of the maximum to reset. Current: {100*total_ctx_string_len/7500:.1f}%')
        else:
            # insert a new conversation func here
            await new_conversation(default_channel, False)


async def new_conversation(default_channel, length_reached):
    global convo_log_count
    global total_ctx_string_len
    convo_log_count += 1


    with open(f'{path}/conversation_logs_{convo_log_count}.json', 'w') as f:
        json.dump([], f, indent=4)
    if length_reached:
        # print('Context length reached. Starting new conversation.')
        await default_channel.send('Context length reached. Starting new conversation.')
        # get gpt-4 to summarize the entire conversation
        with open(f'{path}/conversation_logs_{convo_log_count-1}.json', 'r') as f:
            new_conv_context = json.load(f)
        response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "system", "content": f"Summarize the what was discussed and asked in the following conversation: {new_conv_context}"}]
                )
        response = response['choices'][0]["message"]['content']
        summary = response

        with open('info.json', 'r') as f:
            info = json.load(f)
        conservations = info[0]

        next_key = str(len(conservations))

        info[0][str(convo_log_count-1)]['summarization'] = summary

        new_entry = {
            "total_length": 0,
            "summarization": ""
        }

        conservations[next_key] = new_entry

        info[0] = conservations
        with open('info.json', 'w') as f:
            json.dump(info, f, indent=4)

        with open(f'{path}/conversation_logs_{convo_log_count}.json', 'w') as f:
            json.dump([{"role": "system", "content": f"{summary}"}], f, indent=4) 
        
    else:
        # print('Started new conversation.')

        with open(f'{path}/conversation_logs_{convo_log_count-1}.json', 'r') as f:
            new_conv_context = json.load(f)
        response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "system", "content": f"Summarize the what was discussed and asked in the following conversation: {new_conv_context}"}]
                )
        response = response['choices'][0]["message"]['content']
        summary = response
        with open('info.json', 'r') as f:
            info = json.load(f)
        conservations = info[0]

        next_key = str(len(conservations))

        info[0][str(convo_log_count-1)]['summarization'] = summary

        new_entry = {
            "total_length": 0,
            "summarization": ""
        }

        conservations[next_key] = new_entry

        info[0] = conservations
        with open('info.json', 'w') as f:
            json.dump(info, f, indent=4)
        context = sys_prompt
        with open(f'{path}/conversation_logs_{convo_log_count}.json', 'w') as f:
            json.dump(context, f, indent=4) 
        await default_channel.send('Started new conversation.')
    

client.run(os.getenv("DISCORD_TOKEN"))
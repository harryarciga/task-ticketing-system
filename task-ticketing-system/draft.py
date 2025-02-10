import discord
from discord.ext import commands

from apikeys import *  # Replace with your actual API keys module

# Set up intents and the bot
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

@client.event
async def on_ready():
    print("The bot is now ready for use!")
    print("-----------------------------")

    # Specify the channel ID where the embed should be sent
    channel_id = 1302238822720868374  # Replace with your channel ID
    channel = client.get_channel(channel_id)


    # Create an embed
    embed = discord.Embed(
        title="UP CAPES Task Ticketing System",
        description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
        color=0xffcc1a
    )

    # Create a custom view with buttons
    view = MyView()

    # Send the embed with buttons
    await channel.send(embed=embed, view=view)

# Custom view for interactive buttons
class MyView(discord.ui.View):
    @discord.ui.button(label="Create Task", style=discord.ButtonStyle.primary)
    async def create_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        forms = TaskCreationForms()
        await interaction.response.send_modal(forms)

    @discord.ui.button(label="Edit Task", style=discord.ButtonStyle.secondary)
    async def edit_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Task editing functionality is not implemented yet!", ephemeral=True)


class TaskCreationForms(discord.ui.Modal, title="Create Task"):
    task_name = discord.ui.TextInput(
        label="Task Name",
        placeholder="Enter the task name here...",
        required=True,
        max_length=100
    )

    task_description = discord.ui.TextInput(
        label="Task Description",
        placeholder="Enter a brief description of the task...",
        required=False,
        style=discord.TextStyle.paragraph
    )

    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="YYYY-MM-DD",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Handle the form submission
        embed = discord.Embed(
            title="New Task Created",
            description=f"**Task Name:** {self.task_name}\n"
                        f"**Description:** {self.task_description}\n"
                        f"**Due Date:** {self.due_date}",
            color=0x00ff00
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)




# Run the bot
client.run(BOTTOKEN)  # Replace BOTTOKEN with your actual bot token
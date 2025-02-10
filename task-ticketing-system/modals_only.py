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
    task_context = discord.ui.TextInput(
        label = "Task Context",
        placeholder = "Enter the task context here...\n(Choose between: Year-long, One-time, Taiwan, CAPES Week, Upskill, JobFair, Mixer)",
        required = True,
        max_length = 100
    )

    task_description = discord.ui.TextInput(
        label = "Task Description",
        placeholder = "Enter a brief description of the task...\n(ex: Promo Video, Email Automation, etc.)",
        required = True,
        style = discord.TextStyle.paragraph
    )

    priority = discord.ui.TextInput(
        label = "Priority",
        placeholder = "Enter the priority level of the task...\n(Choose between: P0 - Critical, P1 - High, P2 - Moderate, P3 - Low, P4 - Optional)",
        required = True,
        max_length = 50
        )

    requesting_committee = discord.ui.TextInput(
        label = "Requesting Committee",
        placeholder = "Choose between: SB, CM, CX, HR, IT, MK, FS."
        required = True,
        max_length = 2
        )

    committee_responsible = discord.ui.TextInput(
        label = "Committee Responsible",
        placeholder = "Choose between: SB, CM, CX, HR, IT, MK, FS."
        required = True,
        max_length = 2
        )

    subcommittee_responsible = discord.ui.TextIn



    due_date = discord.ui.TextInput(
        label="Due Date",
        placeholder="MM-DD-YYYY",
        required=True
    )

    #ito na yung para sa form submission
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
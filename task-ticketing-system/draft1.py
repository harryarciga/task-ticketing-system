import discord
import time
from discord.ext import commands

from googleapiclient.discovery import build
from google.oauth2 import service_account


from apikeys import *  # Replace with your actual API keys module


SERVICE_ACCOUNT_FILE = "/home/harryarciga/task-ticketing-system/credentials.json"  # Update with your key's path
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1DLGU03Z-3UxcL-zUGQcv34VonNVQ8tZ8YUaBj3KdSHM"  # Replace with your sheet ID
RANGE_NAME = "Tickets!B12:B503"  # Adjust the range as needed (e.g., Sheet1!A:H)

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("sheets", "v4", credentials=credentials)




# Set up intents and the bot
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

def add_to_google_sheets(data):
    values = [data]
    body = {"values": values}
    try:
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updates').get('updatedRows')} rows appended.")
    except Exception as e:
        print(f"Error appending to Google Sheets: {e}")



@client.event
async def on_ready():
    print("The bot is now ready for use!")
    print("-----------------------------")

    # Specify the channel ID where the embed should be sent
    channel_id = 1302238822720868374  # Replace with your channel ID
    channel = client.get_channel(channel_id)

    if channel:
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
    else:
        print(f"Channel with ID {channel_id} not found.")

# Ito yung nasa start na part
class MyView(discord.ui.View):
    @discord.ui.button(label="Create Task", style=discord.ButtonStyle.primary)
    async def create_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        context = TaskContext()
        await interaction.response.send_message("Select the **context** of the task:", view=context, ephemeral=True)

    @discord.ui.button(label="Edit Task", style=discord.ButtonStyle.secondary)
    async def edit_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Task editing functionality is not implemented yet!", ephemeral=True)


class TaskContext(discord.ui.View):
    @discord.ui.button(label="Year-long", style=discord.ButtonStyle.primary)
    async def year_long_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"You selected **Year-long** as the task context.\nPlease type your **task description** in the chatbox below.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        # Wait for the user to input the task description
        msg = await client.wait_for("message", check=check)
        task_name = msg.content  # Extract the task description

        await interaction.followup.send(
            "Select the **priority** of the task:",
            view=Priority("Year-long", task_name),
            ephemeral=True
        )


    @discord.ui.button(label="One-time", style=discord.ButtonStyle.secondary)
    async def one_time_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"You selected **One-time** as the task context.\nPlease type your **task description** in the chatbox below.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        # Wait for the user to input the task description
        msg = await client.wait_for("message", check=check)
        task_name = msg.content  # Extract the task description

        await interaction.followup.send(
            "Select the **priority** of the task:",
            view=Priority("One-time", task_name),
            ephemeral=True
        )

    @discord.ui.button(label="Taiwan", style=discord.ButtonStyle.success)
    async def taiwan_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"You selected **Taiwan** as the task context.\nPlease type your **task description** in the chatbox below.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        # Wait for the user to input the task description
        msg = await client.wait_for("message", check=check)
        task_name = msg.content  # Extract the task description

        await interaction.followup.send(
            "Select the **priority** of the task:",
            view=Priority("Taiwan", task_name),
            ephemeral=True
        )

    @discord.ui.button(label="CAPES Week", style=discord.ButtonStyle.primary)
    async def capes_week_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"You selected **CAPES Week** as the task context.\nPlease type your **task description** in the chatbox below.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        # Wait for the user to input the task description
        msg = await client.wait_for("message", check=check)
        task_name = msg.content  # Extract the task description

        await interaction.followup.send(
            "Select the **priority** of the task:",
            view=Priority("CAPES Week", task_name),
            ephemeral=True
        )

    @discord.ui.button(label="Upskill", style=discord.ButtonStyle.secondary)
    async def upskill_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"You selected **Upskill** as the task context.\nPlease type your **task description** in the chatbox below.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        # Wait for the user to input the task description
        msg = await client.wait_for("message", check=check)
        task_name = msg.content  # Extract the task description

        await interaction.followup.send(
            "Select the **priority** of the task:",
            view=Priority("Upskill", task_name),
            ephemeral=True
        )

    @discord.ui.button(label="JobFair", style=discord.ButtonStyle.success)
    async def jobfair_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"You selected **JobFair** as the task context.\nPlease type your **task description** in the chatbox below.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        # Wait for the user to input the task description
        msg = await client.wait_for("message", check=check)
        task_name = msg.content  # Extract the task description

        await interaction.followup.send(
            "Select the **priority** of the task:",
            view=Priority("JobFair", task_name),
            ephemeral=True
        )

    @discord.ui.button(label="Mixer", style=discord.ButtonStyle.primary)
    async def mixer_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"You selected **Mixer** as the task context.\nPlease type your **task description** in the chatbox below.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        # Wait for the user to input the task description
        msg = await client.wait_for("message", check=check)
        task_name = msg.content  # Extract the task description

        await interaction.followup.send(
            "Select the **priority** of the task:",
            view=Priority("Mixer", task_name),
            ephemeral=True
        )


class Priority(discord.ui.View):
    def __init__(self, context, task_name):
        self.context = context
        self.task_name = task_name
        super().__init__(timeout=180)

    @discord.ui.button(label="P0 - Critical", style=discord.ButtonStyle.danger)
    async def critical(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee requesting** the task:", view=RequestingCommittee(self.context, self.task_name, "P0 - Critical"), ephemeral=True)

    @discord.ui.button(label="P1 - High", style=discord.ButtonStyle.secondary)
    async def high(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee requesting** the task:", view=RequestingCommittee(self.context, self.task_name, "P1 - High"), ephemeral=True)

    @discord.ui.button(label="P2 - Moderate", style=discord.ButtonStyle.success)
    async def moderate(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee requesting** the task:", view=RequestingCommittee(self.context, self.task_name, "P2 - Moderate"), ephemeral=True)

    @discord.ui.button(label="P3 - Low", style=discord.ButtonStyle.primary)
    async def low(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee requesting** the task:", view=RequestingCommittee(self.context, self.task_name, "P3 - Low"), ephemeral=True)

    @discord.ui.button(label="P4 - Optional", style=discord.ButtonStyle.secondary)
    async def optional(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee requesting** the task:", view=RequestingCommittee(self.context, self.task_name, "P4 - Optional"), ephemeral=True)


class RequestingCommittee(discord.ui.View):
    def __init__(self, context, task_name, priority):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        super().__init__(timeout=180)

    @discord.ui.button(label="SB", style=discord.ButtonStyle.primary)
    async def request_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=CommitteeResponsible(self.context, self.task_name, self.priority, "SB"), ephemeral=True)

    @discord.ui.button(label="CM", style=discord.ButtonStyle.secondary)
    async def request_CM(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=CommitteeResponsible(self.context, self.task_name, self.priority, "CM"), ephemeral=True)

    @discord.ui.button(label="CX", style=discord.ButtonStyle.success)
    async def request_CX(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=CommitteeResponsible(self.context, self.task_name, self.priority, "CX"), ephemeral=True)

    @discord.ui.button(label="HR", style=discord.ButtonStyle.primary)
    async def request_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=CommitteeResponsible(self.context, self.task_name, self.priority, "HR"), ephemeral=True)

    @discord.ui.button(label="IT", style=discord.ButtonStyle.secondary)
    async def request_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=CommitteeResponsible(self.context, self.task_name, self.priority, "IT"), ephemeral=True)

    @discord.ui.button(label="MK", style=discord.ButtonStyle.success)
    async def request_MK(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=CommitteeResponsible(self.context, self.task_name, self.priority, "MK"), ephemeral=True)

    @discord.ui.button(label="FS", style=discord.ButtonStyle.primary)
    async def request_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=CommitteeResponsible(self.context, self.task_name, self.priority, "FS"), ephemeral=True)


class CommitteeResponsible(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        super().__init__(timeout=180)

    @discord.ui.button(label="SB", style=discord.ButtonStyle.primary)
    async def responsible_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=SubcommitteeResponsibleSB(self.context, self.task_name, self.priority, self.requesting_committee, "SB"), ephemeral=True)

    @discord.ui.button(label="CM", style=discord.ButtonStyle.secondary)
    async def responsible_CM(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=SubcommitteeResponsibleCM(self.context, self.task_name, self.priority, self.requesting_committee, "CM"), ephemeral=True)

    @discord.ui.button(label="CX", style=discord.ButtonStyle.success)
    async def responsible_CX(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=SubcommitteeResponsibleCX(self.context, self.task_name, self.priority, self.requesting_committee, "CX"), ephemeral=True)

    @discord.ui.button(label="HR", style=discord.ButtonStyle.primary)
    async def responsible_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=SubcommitteeResponsibleHR(self.context, self.task_name, self.priority, self.requesting_committee, "HR"), ephemeral=True)

    @discord.ui.button(label="IT", style=discord.ButtonStyle.secondary)
    async def responsible_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=SubcommitteeResponsibleIT(self.context, self.task_name, self.priority, self.requesting_committee, "IT"), ephemeral=True)

    @discord.ui.button(label="MK", style=discord.ButtonStyle.success)
    async def responsible_MK(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=SubcommitteeResponsibleMK(self.context, self.task_name, self.priority, self.requesting_committee, "MK"), ephemeral=True)

    @discord.ui.button(label="FS", style=discord.ButtonStyle.primary)
    async def responsible_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **committee assigned or responsible** for the task:", view=SubcommitteeResponsibleFS(self.context, self.task_name, self.priority, self.requesting_committee, "FS"), ephemeral=True)


class SubcommitteeResponsibleSB(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee, committee_responsible):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        super().__init__(timeout=180)

    @discord.ui.button(label="President (SB)", style=discord.ButtonStyle.primary)
    async def president_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "President (SB)"), ephemeral=True)

    @discord.ui.button(label="Executive Vice President (SB)", style=discord.ButtonStyle.secondary)
    async def evp_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Executive Vice President (SB)"), ephemeral=True)

    @discord.ui.button(label="Process Excellence (SB)", style=discord.ButtonStyle.success)
    async def process_ex_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Process Excellence (SB)"), ephemeral=True)

    @discord.ui.button(label="University Affairs (SB)", style=discord.ButtonStyle.primary)
    async def university_affairs_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "University Affairs (SB)"), ephemeral=True)


class SubcommitteeResponsibleCM(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee, committee_responsible):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        super().__init__(timeout=180)

    @discord.ui.button(label="Vice President (CM)", style=discord.ButtonStyle.primary)
    async def vp_CM(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Vice President (CM)"), ephemeral=True)

    @discord.ui.button(label="Brand Management (CM)", style=discord.ButtonStyle.secondary)
    async def brand_CM(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Brand Management (CM)"), ephemeral=True)

    @discord.ui.button(label="External Communications (CM)", style=discord.ButtonStyle.success)
    async def external_CM(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "External Communications (CM)"), ephemeral=True)


class SubcommitteeResponsibleCX(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee, committee_responsible):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        super().__init__(timeout=180)

    @discord.ui.button(label="Vice President (CX)", style=discord.ButtonStyle.primary)
    async def vp_CX(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Vice President (CX)"), ephemeral=True)

    @discord.ui.button(label="Customer Development (CX)", style=discord.ButtonStyle.secondary)
    async def customer_CX(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Customer Development (CX)"), ephemeral=True)

    @discord.ui.button(label="Sales (CX)", style=discord.ButtonStyle.success)
    async def sales_CX(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Sales (CX)"), ephemeral=True)


class SubcommitteeResponsibleHR(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee, committee_responsible):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        super().__init__(timeout=180)

    @discord.ui.button(label="Vice President (HR)", style=discord.ButtonStyle.primary)
    async def vp_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Vice President (HR)"), ephemeral=True)

    @discord.ui.button(label="Performance Management (HR)", style=discord.ButtonStyle.secondary)
    async def performance_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Performance Management (HR)"), ephemeral=True)

    @discord.ui.button(label="Membership (HR)", style=discord.ButtonStyle.success)
    async def membership_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Membership (HR)"), ephemeral=True)

    @discord.ui.button(label="Organization Management (HR)", style=discord.ButtonStyle.primary)
    async def org_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Organization Management (HR)"), ephemeral=True)


class SubcommitteeResponsibleIT(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee, committee_responsible):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        super().__init__(timeout=180)

    @discord.ui.button(label="Vice President (IT)", style=discord.ButtonStyle.primary)
    async def vp_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Vice President (IT)"), ephemeral=True)

    @discord.ui.button(label="Web Development (IT)", style=discord.ButtonStyle.secondary)
    async def web_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Web Development (IT)"), ephemeral=True)

    @discord.ui.button(label="Information Systems (IT)", style=discord.ButtonStyle.success)
    async def info_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Information Systems (IT)"), ephemeral=True)

    @discord.ui.button(label="Automation (IT)", style=discord.ButtonStyle.primary)
    async def auto_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Automation (IT)"), ephemeral=True)


class SubcommitteeResponsibleMK(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee, committee_responsible):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        super().__init__(timeout=180)

    @discord.ui.button(label="Vice President (MK)", style=discord.ButtonStyle.primary)
    async def vp_MK(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Vice President (MK)"), ephemeral=True)

    @discord.ui.button(label="External Relations (MK)", style=discord.ButtonStyle.secondary)
    async def exte_MK(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "External Operations (MK)"), ephemeral=True)

    @discord.ui.button(label="Marketing Operations (MK)", style=discord.ButtonStyle.success)
    async def market_MK(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Marketing Operations (MK)"), ephemeral=True)


class SubcommitteeResponsibleFS(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee, committee_responsible):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        super().__init__(timeout=180)

    @discord.ui.button(label="Vice President (FS)", style=discord.ButtonStyle.primary)
    async def vp_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Vice President (FS)"), ephemeral=True)

    @discord.ui.button(label="Events Operations (FS)", style=discord.ButtonStyle.secondary)
    async def events_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Events Operations (FS)"), ephemeral=True)

    @discord.ui.button(label="External Operations (FS)", style=discord.ButtonStyle.success)
    async def exte_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "External Operations (FS)"), ephemeral=True)

    @discord.ui.button(label="Taiwan (FS)", style=discord.ButtonStyle.primary)
    async def taiwan_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Taiwan (FS)"), ephemeral=True)

    @discord.ui.button(label="CAPES Week (FS)", style=discord.ButtonStyle.secondary)
    async def capes_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "CAPES Week (FS)"), ephemeral=True)

    @discord.ui.button(label="Upskill (FS)", style=discord.ButtonStyle.success)
    async def upskill_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Upskill (FS)"), ephemeral=True)

    @discord.ui.button(label="JobFair (FS)", style=discord.ButtonStyle.primary)
    async def jobfair_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "JobFair (FS)"), ephemeral=True)

    @discord.ui.button(label="Mixer (FS)", style=discord.ButtonStyle.secondary)
    async def mixer_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Select the **subcommittee receiving the output** of the task:", view=ReceivingCommittee(self.context, self.task_name, self.priority, self.requesting_committee, self.committee_responsible, "Mixer (FS)"), ephemeral=True)


class ReceivingCommittee(discord.ui.View):
    def __init__(self, context, task_name, priority, requesting_committee, committee_responsible, subcommittee_responsible):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        super().__init__(timeout=180)

    @discord.ui.button(label="SB", style=discord.ButtonStyle.primary)
    async def receiving_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
            ephemeral=True,
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        deadline_msg = await client.wait_for("message", check=check)
        deadline = deadline_msg.content

        await interaction.followup.send(
            "Is there anything you want to be noted?\nWrite N/A if None",
            ephemeral=True,
        )

        notes_msg = await client.wait_for("message", check=check)
        notes = notes_msg.content

        embed = discord.Embed(
            title="New Task Created!",
            description=(
                f"**Task ID:** 2425-00011\n"
                f"**Task Name:** {self.task_name}\n"
                f"**Task Context:** {self.context}\n"
                f"**Task Priority:** {self.priority}\n"
                f"**Requesting Committee:** {self.requesting_committee}\n"
                f"**Committee Responsible:** {self.committee_responsible}\n"
                f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                f"**Receiving Committee:** SB\n"
                f"**Due Date:** {deadline}\n"
                f"**Notes:** {notes}"
            ),
            color=0xffcc1a,)

        add_to_google_sheets([
            self.context,
            self.task_name,
            self.priority,
            "Unseen",
            self.requesting_committee,
            self.committee_responsible,
            self.subcommittee_responsible,
            "SB",
            "",
            deadline,
            notes,
        ])
        

        await interaction.followup.send(embed=embed, ephemeral=True)

        channel_id = 1302238822720868374  # Replace with your channel ID
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
            color=0xffcc1a
        )

        view = MyView()

        time.sleep(2)

        await channel.send(embed=embed, view=view)

    @discord.ui.button(label="CM", style=discord.ButtonStyle.secondary)
    async def receiving_CM(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please type the **deadline**  for the task in this format:\nMM/DD/YYYY HH:MM",
            ephemeral=True,
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        deadline_msg = await client.wait_for("message", check=check)
        deadline = deadline_msg.content

        await interaction.followup.send(
            "Is there anything you want to be noted?\nWrite N/A if None",
            ephemeral=True,
        )

        notes_msg = await client.wait_for("message", check=check)
        notes = notes_msg.content

        embed = discord.Embed(
            title="New Task Created!",
            description=(
                f"**Task ID:** 2425-00011\n"
                f"**Task Name:** {self.task_name}\n"
                f"**Task Context:** {self.context}\n"
                f"**Task Priority:** {self.priority}\n"
                f"**Requesting Committee:** {self.requesting_committee}\n"
                f"**Committee Responsible:** {self.committee_responsible}\n"
                f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                f"**Receiving Committee:** CM\n"
                f"**Due Date:** {deadline}\n"
                f"**Notes:** {notes}"
            ),
            color=0xffcc1a,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        channel_id = 1302238822720868374  # Replace with your channel ID
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
            color=0xffcc1a,
        )

        view = MyView()

        time.sleep(2)

        await channel.send(embed=embed, view=view)

    @discord.ui.button(label="CX", style=discord.ButtonStyle.success)
    async def receiving_CX(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
            ephemeral=True,
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        deadline_msg = await client.wait_for("message", check=check)
        deadline = deadline_msg.content

        await interaction.followup.send(
            "Is there anything you want to be noted?\nWrite N/A if None",
            ephemeral=True,
        )

        notes_msg = await client.wait_for("message", check=check)
        notes = notes_msg.content

        embed = discord.Embed(
            title="New Task Created!",
            description=(
                f"**Task ID:** 2425-00011\n"
                f"**Task Name:** {self.task_name}\n"
                f"**Task Context:** {self.context}\n"
                f"**Task Priority:** {self.priority}\n"
                f"**Requesting Committee:** {self.requesting_committee}\n"
                f"**Committee Responsible:** {self.committee_responsible}\n"
                f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                f"**Receiving Committee:** CX\n"
                f"**Due Date:** {deadline}\n"
                f"**Notes:** {notes}"
            ),
            color=0xffcc1a,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        channel_id = 1302238822720868374  # Replace with your channel ID
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
            color=0xffcc1a
        )

        view = MyView()

        time.sleep(2)

        await channel.send(embed=embed, view=view)

    @discord.ui.button(label="HR", style=discord.ButtonStyle.primary)
    async def receiving_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
            ephemeral=True,
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        deadline_msg = await client.wait_for("message", check=check)
        deadline = deadline_msg.content

        await interaction.followup.send(
            "Is there anything you want to be noted?\nWrite N/A if None",
            ephemeral=True,
        )

        notes_msg = await client.wait_for("message", check=check)
        notes = notes_msg.content

        embed = discord.Embed(
            title="New Task Created!",
            description=(
                f"**Task ID:** 2425-00011\n"
                f"**Task Name:** {self.task_name}\n"
                f"**Task Context:** {self.context}\n"
                f"**Task Priority:** {self.priority}\n"
                f"**Requesting Committee:** {self.requesting_committee}\n"
                f"**Committee Responsible:** {self.committee_responsible}\n"
                f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                f"**Receiving Committee:** HR\n"
                f"**Due Date:** {deadline}\n"
                f"**Notes:** {notes}"
            ),
            color=0xffcc1a,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        channel_id = 1302238822720868374  # Replace with your channel ID
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
            color=0xffcc1a
        )

        view = MyView()

        time.sleep(2)

        await channel.send(embed=embed, view=view)

    @discord.ui.button(label="IT", style=discord.ButtonStyle.secondary)
    async def receiving_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
                "Please type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        deadline_msg = await client.wait_for("message", check=check)
        deadline = deadline_msg.content

        await interaction.followup.send(  # Changed from send_message to send
            "Is there anything you want to be noted?\nWrite N/A if None",
            ephemeral=True,
        )

        notes_msg = await client.wait_for("message", check=check)
        notes = notes_msg.content

        embed = discord.Embed(
            title="New Task Created!",
            description=(
                f"**Task ID:** 2425-00011\n"
                f"**Task Name:** {self.task_name}\n"
                f"**Task Context:** {self.context}\n"
                f"**Task Priority:** {self.priority}\n"
                f"**Requesting Committee:** {self.requesting_committee}\n"
                f"**Committee Responsible:** {self.committee_responsible}\n"
                f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                f"**Receiving Committee:** IT\n"
                f"**Due Date:** {deadline}\n"
                f"**Notes:** {notes}"
            ),
            color=0xffcc1a,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)  # Changed from send_message to send

        channel_id = 1302238822720868374  # Replace with your channel ID
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
        title="UP CAPES Task Ticketing System",
        description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
        color=0xffcc1a
        )
        
        view = MyView()

        time.sleep(2)

        await channel.send(embed = embed, view=view)

    @discord.ui.button(label="MK", style=discord.ButtonStyle.success)
    async def receiving_MK(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
                "Please type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        deadline_msg = await client.wait_for("message", check=check)
        deadline = deadline_msg.content

        await interaction.followup.send(  # Changed from send_message to send
            "Is there anything you want to be noted?\nWrite N/A if None",
            ephemeral=True,
        )

        notes_msg = await client.wait_for("message", check=check)
        notes = notes_msg.content

        embed = discord.Embed(
            title="New Task Created!",
            description=(
                f"**Task ID:** 2425-00011\n"
                f"**Task Name:** {self.task_name}\n"
                f"**Task Context:** {self.context}\n"
                f"**Task Priority:** {self.priority}\n"
                f"**Requesting Committee:** {self.requesting_committee}\n"
                f"**Committee Responsible:** {self.committee_responsible}\n"
                f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                f"**Receiving Committee:** MK\n"
                f"**Due Date:** {deadline}\n"
                f"**Notes:** {notes}"
            ),
            color=0xffcc1a,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)  # Changed from send_message to send

        channel_id = 1302238822720868374  # Replace with your channel ID
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
        title="UP CAPES Task Ticketing System",
        description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
        color=0xffcc1a
        )
        
        view = MyView()

        time.sleep(2)

        await channel.send(embed = embed, view=view)

    @discord.ui.button(label="FS", style=discord.ButtonStyle.primary)
    async def receiving_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
                "Please type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        deadline_msg = await client.wait_for("message", check=check)
        deadline = deadline_msg.content

        await interaction.followup.send(  # Changed from send_message to send
            "Is there anything you want to be noted?\nWrite N/A if None",
            ephemeral=True,
        )

        notes_msg = await client.wait_for("message", check=check)
        notes = notes_msg.content

        embed = discord.Embed(
            title="New Task Created!",
            description=(
                f"**Task ID:** 2425-00011\n"
                f"**Task Name:** {self.task_name}\n"
                f"**Task Context:** {self.context}\n"
                f"**Task Priority:** {self.priority}\n"
                f"**Requesting Committee:** {self.requesting_committee}\n"
                f"**Committee Responsible:** {self.committee_responsible}\n"
                f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                f"**Receiving Committee:** FS\n"
                f"**Due Date:** {deadline}\n"
                f"**Notes:** {notes}"
            ),
            color=0xffcc1a,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)  # Changed from send_message to send

        channel_id = 1302238822720868374  # Replace with your channel ID
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
        title="UP CAPES Task Ticketing System",
        description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
        color=0xffcc1a
        )
        
        view = MyView()

        time.sleep(2)

        await channel.send(embed = embed, view=view)



#
client.run(BOTTOKEN)  # Replace BOTTOKEN with your actual bot token
#
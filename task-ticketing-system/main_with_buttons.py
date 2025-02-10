import discord
import time
from discord.ext import commands
import re

from googleapiclient.discovery import build
from google.oauth2 import service_account


from apikeys import *  # Replace with your actual API keys module


SERVICE_ACCOUNT_FILE = "/home/harryarciga/task-ticketing-system/credentials.json"  # Update with your key's path
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1DLGU03Z-3UxcL-zUGQcv34VonNVQ8tZ8YUaBj3KdSHM"  # Replace with your sheet ID
RANGE_NAME = "Tickets!B12:B"  # Adjust the range as needed (e.g., Sheet1!A:H)

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("sheets", "v4", credentials=credentials)




# Set up intents and the bot
intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

def get_next_task_id():
    try:
        # Get all values in column A (Task IDs)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Tickets!A:A"  # Adjust the range if needed
        ).execute()

        values = result.get("values", [])
        if not values or not values[0]:  # If column A is empty
            return "2425-00001"  # Start with the first Task ID

        # Extract the last non-empty Task ID
        last_task_id = values[-1][0]

        # Increment the numeric portion
        prefix, num = last_task_id.split("-")
        next_num = int(num) + 1
        return f"{prefix}-{next_num:05d}"  # Maintain leading zeros

    except Exception as e:
        print(f"Error fetching the last task ID: {e}")
        return "2425-00001"  # Fallback to the first Task ID

def add_to_google_sheets(data):
    values = [data]
    body = {"values": values}
    try:
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=SPREADSHEET_ID,
                range="Tickets!A:L",  # Adjust range if necessary
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updates').get('updatedRows')} rows appended.")
    except Exception as e:
        print(f"Error appending to Google Sheets: {e}")

def update_task_in_google_sheets(task_id, updated_data):
    try:
        # Fetch all rows from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Tickets!A:L"  # Adjust the range to cover all relevant columns
        ).execute()

        rows = result.get("values", [])
        
        # Check if header exists
        if not rows:
            print("Sheet is empty or range is invalid.")
            return
        
        # Find the row with the matching Task ID
        row_index = None
        for index, row in enumerate(rows):
            if row and row[0] == task_id:  # Assuming Task ID is in the first column
                row_index = index + 1  # Adjust for 1-based indexing
                break

        if row_index is None:
            print(f"Task ID {task_id} not found in the sheet.")
            return

        # Define the range to update (specific row)
        update_range = f"Tickets!A{row_index}:L{row_index}"  # Adjust column range as needed

        # Prepare the data for update
        body = {
            "values": [updated_data]  # updated_data should be a list of values
        }

        # Update the row
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=update_range,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

        print(f"Task ID {task_id} successfully updated.")
    except Exception as e:
        print(f"Error updating task in Google Sheets: {e}")


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
        embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
        # Create a custom view with buttons
        view = MyView()

        # Send the embed with buttons
        await channel.send(embed=embed, view=view)
    else:
        print(f"Channel with ID {channel_id} not found.")

# Ito yung nasa start na part
class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Create Task", style=discord.ButtonStyle.primary)
    async def create_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        context = self.add_item(TaskContext())
        await interaction.response.send_message("Please select the **context** of the task:", view=context, ephemeral=True)

    @discord.ui.button(label="Edit Task", style=discord.ButtonStyle.secondary)
    async def edit_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please type the **task ID** of the task you wish to change in the chatbox below with this format:\n2425-XXXXX",
            ephemeral=True,
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        while True:
            msg = await client.wait_for("message", check=check)
            task_id = msg.content.strip()  # Extract the task ID
            await msg.delete() 

            try:
                # Get all rows from the sheet
                result = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range="Tickets!A:L"  # Adjust range to include Task ID and all details
                ).execute()

                rows = result.get("values", [])
                headers = rows[0]  # Assuming the first row contains column headers
                data_rows = rows[1:]  # Exclude the header row

                # Find the row with the given Task ID
                task_details = None
                for row in data_rows:
                    if len(row) > 0 and row[0] == task_id:  # Ensure Task ID matches
                        task_details = row
                        break

                if task_details:
                    # Task ID found, save details into variables
                    (
                        task_context,
                        task_description,
                        task_priority,
                        task_status,
                        requesting_committee,
                        committee_responsible,
                        subcommittee_responsible,
                        receiving_committee,
                        resolved_status,
                        deadline,
                        notes,
                    ) = task_details[1:]  # Skip the Task ID (first column)

                    await interaction.followup.send(
                        f"Task ID **{task_id}** found!. Here are the details of the task id:",
                        ephemeral=True,
                    )

                    # Variables are now ready to be passed to another class
                    #### insert embed

                    await interaction.followup.send(
                        f"Is there anything you wish to change on the task details?",
                        view=ToChange(task_id, task_context, task_description, task_priority, task_status, requesting_committee, committee_responsible, subcommittee_responsible, receiving_committee, resolved_status, deadline, notes),
                        ephemeral=True,
                    )

                    break  # Exit loop
                else:
                    # Task ID not found
                    await interaction.followup.send(
                        f"Task ID **{task_id}** was not found. Please try again with a valid Task ID.",
                        ephemeral=True,
                    )
            except Exception as e:
                print(f"Error checking Google Sheets: {e}")
                await interaction.followup.send(
                    "An error occurred while checking the Task ID. Please try again later.",
                    ephemeral=True,
                )
                break  # Exit the loop if an error occurs

        ###### From here, iche-check nung program if meron 
        #### If meron, then ipapakita nung edit_task.py yung details ng task na yun
        #### If wala, show na task_id not found try again chuchu


class TaskContext(discord.ui.Select):
    def __init__(self, task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.task_context = task_context
        self.task_description = task_description
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        #super().__init__(timeout=180)

        options = [
            discord.SelectOption(label="Year-long"),  # you may add description = ""
            discord.SelectOption(label="One-time"),
            discord.SelectOption(label="Taiwan"),
            discord.SelectOption(label="CAPES Week"),
            discord.SelectOption(label="Upskill"),
            discord.SelectOption(label="JobFair"),
            discord.SelectOption(label="Mixer")
        ]
        super().__init__(placeholder="Select the context of the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_context = self.values[0]  # Get the selected context
        if self.change:
            await interaction.response.send_message(
                f"You selected **{selected_context}** as the task context.\nIs there anything you wish to change on the task details?",
                view=ToChange(self.task_id, selected_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
                )

            
        else:
            await interaction.response.send_message(
            f"You selected **{selected_context}** as the task context.\nPlease type your **task description** in the chatbox below.",
            ephemeral=True
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Wait for the user to input the task description
            msg = await client.wait_for("message", check=check)
            task_name = msg.content  # Extract the task description
            await msg.delete() 

            await interaction.followup.send(
                f"You wrote {task_name} as the task description.\nSelect the **priority** of the task:",
                view=Priority(selected_context, task_name),
                ephemeral=True
            )


class Priority(discord.ui.View):
    def __init__(self, task_id="", context="", task_name="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        super().__init__(timeout=180)
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change

    @discord.ui.button(label="P0 - Critical", style=discord.ButtonStyle.danger)
    async def critical(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **P0 - Critical** as the task priority.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, "P0 - Critical", self.task_status,
                    self.requesting_committee, self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **P0 - Critical** as the task priority.\nSelect the **committee requesting** the task:",
                view=RequestingCommittee(self.context, self.task_name, "P0 - Critical"),
                ephemeral=True
            )

    @discord.ui.button(label="P1 - High", style=discord.ButtonStyle.secondary)
    async def high(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **P1 - High** as the task priority.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, "P1 - High", self.task_status,
                    self.requesting_committee, self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **P1 - High** as the task priority.\nSelect the **committee requesting** the task:",
                view=RequestingCommittee(self.context, self.task_name, "P1 - High"),
                ephemeral=True
            )

    @discord.ui.button(label="P2 - Moderate", style=discord.ButtonStyle.success)
    async def moderate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **P2 - Moderate** as the task priority.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, "P2 - Moderate", self.task_status,
                    self.requesting_committee, self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **P2 - Moderate** as the task priority.\nSelect the **committee requesting** the task:",
                view=RequestingCommittee(self.context, self.task_name, "P2 - Moderate"),
                ephemeral=True
            )

    @discord.ui.button(label="P3 - Low", style=discord.ButtonStyle.primary)
    async def low(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **P3 - Low** as the task priority.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, "P3 - Low", self.task_status,
                    self.requesting_committee, self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **P3 - Low** as the task priority.\nSelect the **committee requesting** the task:",
                view=RequestingCommittee(self.context, self.task_name, "P3 - Low"),
                ephemeral=True
            )

    @discord.ui.button(label="P4 - Optional", style=discord.ButtonStyle.secondary)
    async def optional(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **P4 - Optional** as the task priority.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, "P4 - Optional", self.task_status,
                    self.requesting_committee, self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **P4 - Optional** as the task priority.\nSelect the **committee requesting** the task:",
                view=RequestingCommittee(self.context, self.task_name, "P4 - Optional"),
                ephemeral=True
            )


class RequestingCommittee(discord.ui.View):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        super().__init__(timeout=180)
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change

    @discord.ui.button(label="SB", style=discord.ButtonStyle.primary)
    async def request_sb(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **SB** as the committee requesting the task.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, self.priority, self.task_status,
                    "SB", self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **SB** as the committee requesting the task.\nSelect the **committee assigned or responsible** for the task:",
                view=CommitteeResponsible(self.context, self.task_name, self.priority, "SB"),
                ephemeral=True
            )

    @discord.ui.button(label="CM", style=discord.ButtonStyle.secondary)
    async def request_cm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **CM** as the committee requesting the task.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, self.priority, self.task_status,
                    "CM", self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **CM** as the committee requesting the task.\nSelect the **committee assigned or responsible** for the task:",
                view=CommitteeResponsible(self.context, self.task_name, self.priority, "CM"),
                ephemeral=True
            )

    @discord.ui.button(label="CX", style=discord.ButtonStyle.success)
    async def request_cx(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **CX** as the committee requesting the task.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, self.priority, self.task_status,
                    "CX", self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **CX** as the committee requesting the task.\nSelect the **committee assigned or responsible** for the task:",
                view=CommitteeResponsible(self.context, self.task_name, self.priority, "CX"),
                ephemeral=True
            )

    @discord.ui.button(label="HR", style=discord.ButtonStyle.primary)
    async def request_hr(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **HR** as the committee requesting the task.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, self.priority, self.task_status,
                    "HR", self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **HR** as the committee requesting the task.\nSelect the **committee assigned or responsible** for the task:",
                view=CommitteeResponsible(self.context, self.task_name, self.priority, "HR"),
                ephemeral=True
            )

    @discord.ui.button(label="IT", style=discord.ButtonStyle.secondary)
    async def request_it(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **IT** as the committee requesting the task.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, self.priority, self.task_status,
                    "IT", self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **IT** as the committee requesting the task.\nSelect the **committee assigned or responsible** for the task:",
                view=CommitteeResponsible(self.context, self.task_name, self.priority, "IT"),
                ephemeral=True
            )

    @discord.ui.button(label="MK", style=discord.ButtonStyle.success)
    async def request_mk(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **MK** as the committee requesting the task.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, self.priority, self.task_status,
                    "MK", self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **MK** as the committee requesting the task.\nSelect the **committee assigned or responsible** for the task:",
                view=CommitteeResponsible(self.context, self.task_name, self.priority, "MK"),
                ephemeral=True
            )

    @discord.ui.button(label="FS", style=discord.ButtonStyle.primary)
    async def request_fs(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message(
                "You selected **FS** as the committee requesting the task.\nIs there anything you wish to change on the task details?",
                view=ToChange(
                    self.task_id, self.context, self.task_name, self.priority, self.task_status,
                    "FS", self.committee_responsible, self.subcommittee_responsible,
                    self.receiving_committee, self.resolved_status, self.deadline, self.notes
                ),
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "You selected **FS** as the committee requesting the task.\nSelect the **committee assigned or responsible** for the task:",
                view=CommitteeResponsible(self.context, self.task_name, self.priority, "FS"),
                ephemeral=True
            )


class CommitteeResponsible(discord.ui.View):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        super().__init__(timeout=180)

    
    @discord.ui.button(label="SB", style=discord.ButtonStyle.primary)
    async def responsible_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **SB** as the committee responsible for the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, "SB", self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            subcommittee_view = self.add_item(SubcommitteeResponsibleSB(self.context, self.task_name, self.priority, self.requesting_committee, "SB"))
            await interaction.response.send_message("You selected **SB** as the committee assigned for the task.\nSelect the **subcommittee assigned or responsible** for the task:", view=subcommittee_view, ephemeral=True)

    @discord.ui.button(label="CM", style=discord.ButtonStyle.secondary)
    async def responsible_CM(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **CM** as the committee responsible for the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, "CM", self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            subcommittee_view = self.add_item(SubcommitteeResponsibleCM(self.context, self.task_name, self.priority, self.requesting_committee, "CM"))
            await interaction.response.send_message("You selected **CM** as the committee assigned for the task.\nSelect the **subcommittee assigned or responsible** for the task:", view=subcommittee_view, ephemeral=True)

    @discord.ui.button(label="CX", style=discord.ButtonStyle.success)
    async def responsible_CX(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **CX** as the committee responsible for the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, "CX", self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            subcommittee_view = self.add_item(SubcommitteeResponsibleCX(self.context, self.task_name, self.priority, self.requesting_committee, "CX"))
            await interaction.response.send_message("You selected **CX** as the committee assigned for the task.\nSelect the **subcommittee assigned or responsible** for the task:", view=subcommittee_view, ephemeral=True)

    @discord.ui.button(label="HR", style=discord.ButtonStyle.primary)
    async def responsible_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **HR** as the committee responsible for the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, "HR", self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            subcommittee_view = self.add_item(SubcommitteeResponsibleHR(self.context, self.task_name, self.priority, self.requesting_committee, "HR"))
            await interaction.response.send_message("You selected **HR** as the committee assigned for the task.\nSelect the **subcommittee assigned or responsible** for the task:", view=subcommittee_view, ephemeral=True)

    @discord.ui.button(label="IT", style=discord.ButtonStyle.secondary)
    async def responsible_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **IT** as the committee responsible for the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, "IT", self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            subcommittee_view = self.add_item(SubcommitteeResponsibleIT(self.context, self.task_name, self.priority, self.requesting_committee, "IT"))
            await interaction.response.send_message("You selected **IT** as the committee assigned for the task.\nSelect the **subcommittee assigned or responsible** for the task:", view=subcommittee_view, ephemeral=True)

    @discord.ui.button(label="MK", style=discord.ButtonStyle.success)
    async def responsible_MK(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **MK** as the committee responsible for the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, "MK", self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            subcommittee_view = self.add_item(SubcommitteeResponsibleMK(self.context, self.task_name, self.priority, self.requesting_committee, "MK"))
            await interaction.response.send_message("You selected **MK** as the committee assigned for the task.\nSelect the **subcommittee assigned or responsible** for the task:", view=subcommittee_view, ephemeral=True)

    @discord.ui.button(label="FS", style=discord.ButtonStyle.primary)
    async def responsible_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **FS** as the committee responsible for the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, "FS", self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            subcommittee_view = self.add_item(SubcommitteeResponsibleFS(self.context, self.task_name, self.priority, self.requesting_committee, "FS"))
            await interaction.response.send_message("You selected **FS** as the committee assigned for the task.\nSelect the **subcommittee assigned or responsible** for the task:", view=subcommittee_view, ephemeral=True)


class SubcommitteeResponsibleSB(discord.ui.Select):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        #super().__init__(timeout=180)



        options = [
                discord.SelectOption(label="President (SB)"),
                discord.SelectOption(label="Executive Vice President (SB)"),
                discord.SelectOption(label="Process Excellence (SB)"),
                discord.SelectOption(label="University Affairs (SB)")
            ]

        super().__init__(placeholder="Select the subcommittee assigned or responsible for the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_subcommittee = self.values[0]
        if self.change == "yes":
            await interaction.followup.send(
                f"You have selected {selected_subcommittee} as the subcommittee assigned or responsible for the task.",
                view=ToChange(self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            # Transition to the receiving committee dropdown
            await interaction.response.send_message(
                "Select the committee receiving the output of the task:",
                view=ReceivingCommittee(
                    self.context, 
                    self.task_name, 
                    self.priority, 
                    self.requesting_committee, 
                    self.committee_responsible, 
                    selected_subcommittee
                    ),
                ephemeral=True,
            )



class SubcommitteeResponsibleCM(discord.ui.Select):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        #super().__init__(timeout=180)

        options = [
                discord.SelectOption(label="Vice President (CM)"),
                discord.SelectOption(label="Brand Management (CM)"),
                discord.SelectOption(label="External Communications (CM)")
            ]

        super().__init__(placeholder="Select the subcommittee assigned or responsible for the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_subcommittee = self.values[0]
        if self.change == "yes":
            await interaction.followup.send(
                f"You have selected {selected_subcommittee} as the subcommittee assigned or responsible for the task.",
                view=ToChange(self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            # Transition to the receiving committee dropdown
            await interaction.response.send_message(
                "Select the committee receiving the output of the task:",
                view=ReceivingCommittee(
                    self.context, 
                    self.task_name, 
                    self.priority, 
                    self.requesting_committee, 
                    self.committee_responsible, 
                    selected_subcommittee
                    ),
                ephemeral=True,
            )


class SubcommitteeResponsibleCX(discord.ui.Select):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        #super().__init__(timeout=180)

        options = [
                discord.SelectOption(label="Vice President (CX)"),
                discord.SelectOption(label="Customer Development (CX)"),
                discord.SelectOption(label="Sales (CX)")
            ]

        super().__init__(placeholder="Select the subcommittee assigned or responsible for the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_subcommittee = self.values[0]
        if self.change == "yes":
            await interaction.followup.send(
                f"You have selected {selected_subcommittee} as the subcommittee assigned or responsible for the task.",
                view=ToChange(self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            # Transition to the receiving committee dropdown
            await interaction.response.send_message(
                "Select the committee receiving the output of the task:",
                view=ReceivingCommittee(
                    self.context, 
                    self.task_name, 
                    self.priority, 
                    self.requesting_committee, 
                    self.committee_responsible, 
                    selected_subcommittee
                    ),
                ephemeral=True,
            )


class SubcommitteeResponsibleHR(discord.ui.Select):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        #super().__init__(timeout=180)

        options = [
                discord.SelectOption(label="Vice President (HR)"),
                discord.SelectOption(label="Performance Management (HR)"),
                discord.SelectOption(label="Membership (HR)"),
                discord.SelectOption(label="Organization Management (HR)")
            ]

        super().__init__(placeholder="Select the subcommittee assigned or responsible for the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_subcommittee = self.values[0]
        if self.change == "yes":
            await interaction.followup.send(
                f"You have selected {selected_subcommittee} as the subcommittee assigned or responsible for the task.",
                view=ToChange(self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            # Transition to the receiving committee dropdown
            await interaction.response.send_message(
                "Select the committee receiving the output of the task:",
                view=ReceivingCommittee(
                    self.context, 
                    self.task_name, 
                    self.priority, 
                    self.requesting_committee, 
                    self.committee_responsible, 
                    selected_subcommittee
                    ),
                ephemeral=True,
            )



class SubcommitteeResponsibleIT(discord.ui.Select):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        #super().__init__(timeout=180)


        options = [
                discord.SelectOption(label="Vice President (IT)"),
                discord.SelectOption(label="Web Development (IT)"),
                discord.SelectOption(label="Information Systems (IT)"),
                discord.SelectOption(label="Automation (IT)")
            ]

        super().__init__(placeholder="Select the subcommittee assigned or responsible for the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_subcommittee = self.values[0]
        if self.change == "yes":
            await interaction.followup.send(
                f"You have selected {selected_subcommittee} as the subcommittee assigned or responsible for the task.",
                view=ToChange(self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            # Transition to the receiving committee dropdown
            await interaction.response.send_message(
                "Select the committee receiving the output of the task:",
                view=ReceivingCommittee(
                    self.context, 
                    self.task_name, 
                    self.priority, 
                    self.requesting_committee, 
                    self.committee_responsible, 
                    selected_subcommittee
                    ),
                ephemeral=True,
            )

class SubcommitteeResponsibleMK(discord.ui.Select):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        #super().__init__(timeout=180)

        options = [
                discord.SelectOption(label="Vice President (MK)"),
                discord.SelectOption(label="External Relations (MK)"),
                discord.SelectOption(label="Marketing Operations (MK)")
            ]

        super().__init__(placeholder="Select the subcommittee assigned or responsible for the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_subcommittee = self.values[0]
        if self.change == "yes":
            await interaction.followup.send(
                f"You have selected {selected_subcommittee} as the subcommittee assigned or responsible for the task.",
                view=ToChange(self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            # Transition to the receiving committee dropdown
            await interaction.response.send_message(
                "Select the committee receiving the output of the task:",
                view=ReceivingCommittee(
                    self.context, 
                    self.task_name, 
                    self.priority, 
                    self.requesting_committee, 
                    self.committee_responsible, 
                    selected_subcommittee
                    ),
                ephemeral=True,
            )


class SubcommitteeResponsibleFS(discord.ui.Select):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        #super().__init__(timeout=180)

        options = [
                discord.SelectOption(label="Vice President (FS)"),
                discord.SelectOption(label="Events Operations (FS)"),
                discord.SelectOption(label="External Operations (FS)"),
                discord.SelectOption(label="Taiwan (FS)"),
                discord.SelectOption(label="CAPES Week (FS)"),
                discord.SelectOption(label="Upskill (FS)"),
                discord.SelectOption(label="JobFair (FS)"),
                discord.SelectOption(label="Mixer (FS)")
            ]

        super().__init__(placeholder="Select the subcommittee assigned or responsible for the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_subcommittee = self.values[0]
        if self.change == "yes":
            await interaction.followup.send(
                f"You have selected {selected_subcommittee} as the subcommittee assigned or responsible for the task.",
                view=ToChange(self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            # Transition to the receiving committee dropdown
            await interaction.response.send_message(
                "Select the committee receiving the output of the task:",
                view=ReceivingCommittee(
                    self.context, 
                    self.task_name, 
                    self.priority, 
                    self.requesting_committee, 
                    self.committee_responsible, 
                    selected_subcommittee
                    ),
                ephemeral=True,
            )


class ReceivingCommittee(discord.ui.View):
    def __init__(self, task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        super().__init__(timeout=180)


    
    @discord.ui.button(label="SB", style=discord.ButtonStyle.primary)
    async def receiving_SB(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **SB** as the committee receiving the output of the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, "SB", self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            await interaction.response.send_message(
                "You selected **SB** as the committee receiving the output of the task.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Collect deadline
            deadline_msg = await client.wait_for("message", check=check)
            deadline = deadline_msg.content
            await deadline_msg.delete() 
            # Collect notes
            await interaction.followup.send(
                f"You wrote **{deadline}** as the deadline for the task.\nIs there anything you want to be noted?\nWrite **N/A** if None",
                ephemeral=True,
            )

            notes_msg = await client.wait_for("message", check=check)
            notes = notes_msg.content
            await notes_msg.delete() 

            # Collect creator's mention
            await interaction.followup.send(
                f"You wrote **{notes}** as your note. Please mention your Discord account as the creator of this task. Example: @YourName",
                ephemeral=True,
            )
            creator_mention_msg = await client.wait_for("message", check=check)
            creator_mention = creator_mention_msg.content.strip()
            await creator_mention_msg.delete() 

            # Collect responsible persons' mentions
            await interaction.followup.send(
                "Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23",
                ephemeral=True,
            )
            respo_mentions_msg = await client.wait_for("message", check=check)
            respo_mentions = respo_mentions_msg.content.strip()
            await respo_mentions_msg.delete() 

            task_id = get_next_task_id()  # Generate the next Task ID dynamically

            # Create Embed
            embed = discord.Embed(
                title="New Task Created!",
                description=(
                    f"**Task ID:** {task_id}\n"
                    f"**Task Name:** {self.task_name}\n"
                    f"**Task Context:** {self.context}\n"
                    f"**Task Priority:** {self.priority}\n"
                    f"**Requesting Committee:** {self.requesting_committee}\n"
                    f"**Committee Responsible:** {self.committee_responsible}\n"
                    f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                    f"**Receiving Committee:** SB\n"
                    f"**Due Date:** {deadline}\n"
                    f"**Notes:** {notes}\n"
                    f"**Task Creator:** {creator_mention}\n"
                    f"**Person/s in Charge:** {respo_mentions}"
                ),
                color=0xffcc1a,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send Embed to the other server
            target_guild = client.get_guild(1302238411020832780) #Server ID
            target_channel = target_guild.get_channel(1320416019272957993) #Text channel ID

            if target_channel:
                await target_channel.send(embed=embed)
            else:
                print('lala')


            add_to_google_sheets([
                "",
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
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button or modify tasks through the 'Edit Task' button.",
                color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
            
            view = MyView()

            time.sleep(2)

            await channel.send(embed=embed, view=view)


    @discord.ui.button(label="CM", style=discord.ButtonStyle.secondary)
    async def receiving_CM(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **CM** as the committee receiving the output of the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, "CM", self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            await interaction.response.send_message(
                "You selected **CM** as the committee receiving the output of the task.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Collect deadline
            deadline_msg = await client.wait_for("message", check=check)
            deadline = deadline_msg.content
            await deadline_msg.delete() 
            # Collect notes
            await interaction.followup.send(
                f"You wrote **{deadline}** as the deadline for the task.\nIs there anything you want to be noted?\nWrite **N/A** if None",
                ephemeral=True,
            )

            notes_msg = await client.wait_for("message", check=check)
            notes = notes_msg.content
            await notes_msg.delete() 

            # Collect creator's mention
            await interaction.followup.send(
                f"You wrote **{notes}** as your note. Please mention your Discord account as the creator of this task. Example: @YourName",
                ephemeral=True,
            )
            creator_mention_msg = await client.wait_for("message", check=check)
            creator_mention = creator_mention_msg.content.strip()
            await creator_mention_msg.delete() 

            # Collect responsible persons' mentions
            await interaction.followup.send(
                "Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23",
                ephemeral=True,
            )
            respo_mentions_msg = await client.wait_for("message", check=check)
            respo_mentions = respo_mentions_msg.content.strip()
            await respo_mentions_msg.delete() 

            task_id = get_next_task_id()  # Generate the next Task ID dynamically

            # Create Embed
            embed = discord.Embed(
                title="New Task Created!",
                description=(
                    f"**Task ID:** {task_id}\n"
                    f"**Task Name:** {self.task_name}\n"
                    f"**Task Context:** {self.context}\n"
                    f"**Task Priority:** {self.priority}\n"
                    f"**Requesting Committee:** {self.requesting_committee}\n"
                    f"**Committee Responsible:** {self.committee_responsible}\n"
                    f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                    f"**Receiving Committee:** CM\n"
                    f"**Due Date:** {deadline}\n"
                    f"**Notes:** {notes}\n"
                    f"**Task Creator:** {creator_mention}\n"
                    f"**Person/s in Charge:** {respo_mentions}"
                ),
                color=0xffcc1a,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send Embed to the other server
            target_guild = client.get_guild(1302238411020832780) #Server ID
            target_channel = target_guild.get_channel(1320416019272957993) #Text channel ID

            if target_channel:
                await target_channel.send(embed=embed)


            add_to_google_sheets([
                "",
                self.context,
                self.task_name,
                self.priority,
                "Unseen",
                self.requesting_committee,
                self.committee_responsible,
                self.subcommittee_responsible,
                "CM",
                "",
                deadline,
                notes,
            ])

            await interaction.followup.send(embed=embed, ephemeral=True)

            channel_id = 1302238822720868374  # Replace with your channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button or modify tasks through the 'Edit Task' button.",
                color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
            
            view = MyView()

            time.sleep(2)

            await channel.send(embed=embed, view=view)


    @discord.ui.button(label="CX", style=discord.ButtonStyle.success)
    async def receiving_CX(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **CX** as the committee receiving the output of the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, "CX", self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            await interaction.response.send_message(
                "You selected **CX** as the committee receiving the output of the task.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Collect deadline
            deadline_msg = await client.wait_for("message", check=check)
            deadline = deadline_msg.content
            await deadline_msg.delete() 
            # Collect notes
            await interaction.followup.send(
                f"You wrote **{deadline}** as the deadline for the task.\nIs there anything you want to be noted?\nWrite **N/A** if None",
                ephemeral=True,
            )

            notes_msg = await client.wait_for("message", check=check)
            notes = notes_msg.content
            await notes_msg.delete() 

            # Collect creator's mention
            await interaction.followup.send(
                f"You wrote **{notes}** as your note. Please mention your Discord account as the creator of this task. Example: @YourName",
                ephemeral=True,
            )
            creator_mention_msg = await client.wait_for("message", check=check)
            creator_mention = creator_mention_msg.content.strip()
            await creator_mention_msg.delete() 

            # Collect responsible persons' mentions
            await interaction.followup.send(
                "Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23",
                ephemeral=True,
            )
            respo_mentions_msg = await client.wait_for("message", check=check)
            respo_mentions = respo_mentions_msg.content.strip()
            await respo_mentions_msg.delete() 

            task_id = get_next_task_id()  # Generate the next Task ID dynamically

            # Create Embed
            embed = discord.Embed(
                title="New Task Created!",
                description=(
                    f"**Task ID:** {task_id}\n"
                    f"**Task Name:** {self.task_name}\n"
                    f"**Task Context:** {self.context}\n"
                    f"**Task Priority:** {self.priority}\n"
                    f"**Requesting Committee:** {self.requesting_committee}\n"
                    f"**Committee Responsible:** {self.committee_responsible}\n"
                    f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                    f"**Receiving Committee:** CX\n"
                    f"**Due Date:** {deadline}\n"
                    f"**Notes:** {notes}\n"
                    f"**Task Creator:** {creator_mention}\n"
                    f"**Person/s in Charge:** {respo_mentions}"
                ),
                color=0xffcc1a,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send Embed to the other server
            target_guild = client.get_guild(1302238411020832780) #Server ID
            target_channel = target_guild.get_channel(1320416019272957993) #Text channel ID

            if target_channel:
                await target_channel.send(embed=embed)
            else:
                print('lala')


            add_to_google_sheets([
                "",
                self.context,
                self.task_name,
                self.priority,
                "Unseen",
                self.requesting_committee,
                self.committee_responsible,
                self.subcommittee_responsible,
                "CX",
                "",
                deadline,
                notes,
            ])

            await interaction.followup.send(embed=embed, ephemeral=True)

            channel_id = 1302238822720868374  # Replace with your channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button or modify tasks through the 'Edit Task' button.",
                color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
            
            view = MyView()

            time.sleep(2)

            await channel.send(embed=embed, view=view)


    @discord.ui.button(label="HR", style=discord.ButtonStyle.primary)
    async def receiving_HR(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **HR** as the committee receiving the output of the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, "HR", self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            await interaction.response.send_message(
                "You selected **HR** as the committee receiving the output of the task.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Collect deadline
            deadline_msg = await client.wait_for("message", check=check)
            deadline = deadline_msg.content
            await deadline_msg.delete() 
            # Collect notes
            await interaction.followup.send(
                f"You wrote **{deadline}** as the deadline for the task.\nIs there anything you want to be noted?\nWrite **N/A** if None",
                ephemeral=True,
            )

            notes_msg = await client.wait_for("message", check=check)
            notes = notes_msg.content
            await notes_msg.delete() 

            # Collect creator's mention
            await interaction.followup.send(
                f"You wrote **{notes}** as your note. Please mention your Discord account as the creator of this task. Example: @YourName",
                ephemeral=True,
            )
            creator_mention_msg = await client.wait_for("message", check=check)
            creator_mention = creator_mention_msg.content.strip()
            await creator_mention_msg.delete() 

            # Collect responsible persons' mentions
            await interaction.followup.send(
                "Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23",
                ephemeral=True,
            )
            respo_mentions_msg = await client.wait_for("message", check=check)
            respo_mentions = respo_mentions_msg.content.strip()
            await respo_mentions_msg.delete() 

            task_id = get_next_task_id()  # Generate the next Task ID dynamically

            # Create Embed
            embed = discord.Embed(
                title="New Task Created!",
                description=(
                    f"**Task ID:** {task_id}\n"
                    f"**Task Name:** {self.task_name}\n"
                    f"**Task Context:** {self.context}\n"
                    f"**Task Priority:** {self.priority}\n"
                    f"**Requesting Committee:** {self.requesting_committee}\n"
                    f"**Committee Responsible:** {self.committee_responsible}\n"
                    f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                    f"**Receiving Committee:** HR\n"
                    f"**Due Date:** {deadline}\n"
                    f"**Notes:** {notes}\n"
                    f"**Task Creator:** {creator_mention}\n"
                    f"**Person/s in Charge:** {respo_mentions}"
                ),
                color=0xffcc1a,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send Embed to the other server
            target_guild = client.get_guild(1302238411020832780) #Server ID
            target_channel = target_guild.get_channel(1320416019272957993) #Text channel ID

            if target_channel:
                await target_channel.send(embed=embed)
            else:
                print('lala')


            add_to_google_sheets([
                "",
                self.context,
                self.task_name,
                self.priority,
                "Unseen",
                self.requesting_committee,
                self.committee_responsible,
                self.subcommittee_responsible,
                "HR",
                "",
                deadline,
                notes,
            ])

            await interaction.followup.send(embed=embed, ephemeral=True)

            channel_id = 1302238822720868374  # Replace with your channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button or modify tasks through the 'Edit Task' button.",
                color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
            
            view = MyView()

            time.sleep(2)

            await channel.send(embed=embed, view=view)


    @discord.ui.button(label="IT", style=discord.ButtonStyle.secondary)
    async def receiving_IT(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **IT** as the committee receiving the output of the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, "IT", self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            await interaction.response.send_message(
                "You selected **IT** as the committee receiving the output of the task.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Collect deadline
            deadline_msg = await client.wait_for("message", check=check)
            deadline = deadline_msg.content
            await deadline_msg.delete() 
            # Collect notes
            await interaction.followup.send(
                f"You wrote **{deadline}** as the deadline for the task.\nIs there anything you want to be noted?\nWrite **N/A** if None",
                ephemeral=True,
            )

            notes_msg = await client.wait_for("message", check=check)
            notes = notes_msg.content
            await notes_msg.delete() 

            # Collect creator's mention
            await interaction.followup.send(
                f"You wrote **{notes}** as your note. Please mention your Discord account as the creator of this task. Example: @YourName",
                ephemeral=True,
            )
            creator_mention_msg = await client.wait_for("message", check=check)
            creator_mention = creator_mention_msg.content.strip()
            await creator_mention_msg.delete() 

            # Collect responsible persons' mentions
            await interaction.followup.send(
                "Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23",
                ephemeral=True,
            )
            respo_mentions_msg = await client.wait_for("message", check=check)
            respo_mentions = respo_mentions_msg.content.strip()
            await respo_mentions_msg.delete() 

            task_id = get_next_task_id()  # Generate the next Task ID dynamically

            # Create Embed
            embed = discord.Embed(
                title="New Task Created!",
                description=(
                    f"**Task ID:** {task_id}\n"
                    f"**Task Name:** {self.task_name}\n"
                    f"**Task Context:** {self.context}\n"
                    f"**Task Priority:** {self.priority}\n"
                    f"**Requesting Committee:** {self.requesting_committee}\n"
                    f"**Committee Responsible:** {self.committee_responsible}\n"
                    f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                    f"**Receiving Committee:** IT\n"
                    f"**Due Date:** {deadline}\n"
                    f"**Notes:** {notes}\n"
                    f"**Task Creator:** {creator_mention}\n"
                    f"**Person/s in Charge:** {respo_mentions}"
                ),
                color=0xffcc1a,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send Embed to the other server
            target_guild = client.get_guild(1302238411020832780) #Server ID
            target_channel = target_guild.get_channel(1320416019272957993) #Text channel ID

            if target_channel:
                await target_channel.send(embed=embed)
            else:
                print('lala')


            add_to_google_sheets([
                "",
                self.context,
                self.task_name,
                self.priority,
                "Unseen",
                self.requesting_committee,
                self.committee_responsible,
                self.subcommittee_responsible,
                "IT",
                "",
                deadline,
                notes,
            ])

            await interaction.followup.send(embed=embed, ephemeral=True)

            channel_id = 1302238822720868374  # Replace with your channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button or modify tasks through the 'Edit Task' button.",
                color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
            
            view = MyView()

            time.sleep(2)

            await channel.send(embed=embed, view=view)

    @discord.ui.button(label="MK", style=discord.ButtonStyle.success)
    async def receiving_MK(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **MK** as the committee receiving the output of the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, "MK", self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            await interaction.response.send_message(
                "You selected **MK** as the committee receiving the output of the task.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Collect deadline
            deadline_msg = await client.wait_for("message", check=check)
            deadline = deadline_msg.content
            await deadline_msg.delete() 
            # Collect notes
            await interaction.followup.send(
                f"You wrote **{deadline}** as the deadline for the task.\nIs there anything you want to be noted?\nWrite **N/A** if None",
                ephemeral=True,
            )

            notes_msg = await client.wait_for("message", check=check)
            notes = notes_msg.content
            await notes_msg.delete() 

            # Collect creator's mention
            await interaction.followup.send(
                f"You wrote **{notes}** as your note. Please mention your Discord account as the creator of this task. Example: @YourName",
                ephemeral=True,
            )
            creator_mention_msg = await client.wait_for("message", check=check)
            creator_mention = creator_mention_msg.content.strip()
            await creator_mention_msg.delete() 

            # Collect responsible persons' mentions
            await interaction.followup.send(
                "Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23",
                ephemeral=True,
            )
            respo_mentions_msg = await client.wait_for("message", check=check)
            respo_mentions = respo_mentions_msg.content.strip()
            await respo_mentions_msg.delete() 

            task_id = get_next_task_id()  # Generate the next Task ID dynamically

            # Create Embed
            embed = discord.Embed(
                title="New Task Created!",
                description=(
                    f"**Task ID:** {task_id}\n"
                    f"**Task Name:** {self.task_name}\n"
                    f"**Task Context:** {self.context}\n"
                    f"**Task Priority:** {self.priority}\n"
                    f"**Requesting Committee:** {self.requesting_committee}\n"
                    f"**Committee Responsible:** {self.committee_responsible}\n"
                    f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                    f"**Receiving Committee:** MK\n"
                    f"**Due Date:** {deadline}\n"
                    f"**Notes:** {notes}\n"
                    f"**Task Creator:** {creator_mention}\n"
                    f"**Person/s in Charge:** {respo_mentions}"
                ),
                color=0xffcc1a,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send Embed to the other server
            target_guild = client.get_guild(1302238411020832780) #Server ID
            target_channel = target_guild.get_channel(1320416019272957993) #Text channel ID

            if target_channel:
                await target_channel.send(embed=embed)
            else:
                print('lala')


            add_to_google_sheets([
                "",
                self.context,
                self.task_name,
                self.priority,
                "Unseen",
                self.requesting_committee,
                self.committee_responsible,
                self.subcommittee_responsible,
                "MK",
                "",
                deadline,
                notes,
            ])

            await interaction.followup.send(embed=embed, ephemeral=True)

            channel_id = 1302238822720868374  # Replace with your channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button or modify tasks through the 'Edit Task' button.",
                color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
            
            view = MyView()

            time.sleep(2)

            await channel.send(embed=embed, view=view)


    @discord.ui.button(label="FS", style=discord.ButtonStyle.primary)
    async def receiving_FS(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.change:
            await interaction.response.send_message("You selected **FS** as the committee receiving the output of the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.context, self.task_name, self.priority , self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, "FS", self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
                        )
        else:
            await interaction.response.send_message(
                "You selected **FS** as the committee receiving the output of the task.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM",
                ephemeral=True,
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Collect deadline
            deadline_msg = await client.wait_for("message", check=check)
            deadline = deadline_msg.content
            await deadline_msg.delete() 
            # Collect notes
            await interaction.followup.send(
                f"You wrote **{deadline}** as the deadline for the task.\nIs there anything you want to be noted?\nWrite **N/A** if None",
                ephemeral=True,
            )

            notes_msg = await client.wait_for("message", check=check)
            notes = notes_msg.content
            await notes_msg.delete() 

            # Collect creator's mention
            await interaction.followup.send(
                f"You wrote **{notes}** as your note. Please mention your Discord account as the creator of this task. Example: @YourName",
                ephemeral=True,
            )
            creator_mention_msg = await client.wait_for("message", check=check)
            creator_mention = creator_mention_msg.content.strip()
            await creator_mention_msg.delete() 

            # Collect responsible persons' mentions
            await interaction.followup.send(
                "Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23",
                ephemeral=True,
            )
            respo_mentions_msg = await client.wait_for("message", check=check)
            respo_mentions = respo_mentions_msg.content.strip()
            await respo_mentions_msg.delete() 

            task_id = get_next_task_id()  # Generate the next Task ID dynamically

            # Create Embed
            embed = discord.Embed(
                title="New Task Created!",
                description=(
                    f"**Task ID:** {task_id}\n"
                    f"**Task Name:** {self.task_name}\n"
                    f"**Task Context:** {self.context}\n"
                    f"**Task Priority:** {self.priority}\n"
                    f"**Requesting Committee:** {self.requesting_committee}\n"
                    f"**Committee Responsible:** {self.committee_responsible}\n"
                    f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                    f"**Receiving Committee:** FS\n"
                    f"**Due Date:** {deadline}\n"
                    f"**Notes:** {notes}\n"
                    f"**Task Creator:** {creator_mention}\n"
                    f"**Person/s in Charge:** {respo_mentions}"
                ),
                color=0xffcc1a,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send Embed to the other server
            target_guild = client.get_guild(1302238411020832780) #Server ID
            target_channel = target_guild.get_channel(1320416019272957993) #Text channel ID

            if target_channel:
                await target_channel.send(embed=embed)
            else:
                print('lala')


            add_to_google_sheets([
                "",
                self.context,
                self.task_name,
                self.priority,
                "Unseen",
                self.requesting_committee,
                self.committee_responsible,
                self.subcommittee_responsible,
                "FS",
                "",
                deadline,
                notes,
            ])

            await interaction.followup.send(embed=embed, ephemeral=True)

            channel_id = 1302238822720868374  # Replace with your channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button or modify tasks through the 'Edit Task' button.",
                color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
            
            view = MyView()

            time.sleep(2)

            await channel.send(embed=embed, view=view)


class Status(discord.ui.View):
    def __init__(self, task_id="", context="", task_name="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        super().__init__(timeout=180)

    @discord.ui.button(label="Unseen", style=discord.ButtonStyle.danger)
    async def unseen(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You selected **Unseen** as the task status.\nIs there anything you wish to change on the task details?",
                    view=ToChange(self.task_id, self.context, self.task_name, self.task_priority, "Unseen", self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                    ephemeral=True
                    )

    @discord.ui.button(label="Acknowledged", style=discord.ButtonStyle.secondary)
    async def ack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You selected **Acknowledged** as the task status.\nIs there anything you wish to change on the task details?",
                    view=ToChange(self.task_id, self.context, self.task_name, self.task_priority, "Acknowledged", self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                    ephemeral=True
                    )

    @discord.ui.button(label="In Progress", style=discord.ButtonStyle.success)
    async def progress(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You selected **In Progress** as the task status.\nIs there anything you wish to change on the task details?",
                    view=ToChange(self.task_id, self.context, self.task_name, self.task_priority, "In Progress", self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                    ephemeral=True
                    )

    @discord.ui.button(label="Blocked", style=discord.ButtonStyle.primary)
    async def blocked(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You selected **Blocked** as the task status.\nIs there anything you wish to change on the task details?",
                    view=ToChange(self.task_id, self.context, self.task_name, self.task_priority, "Blocked", self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                    ephemeral=True
                    )

    @discord.ui.button(label="Completed", style=discord.ButtonStyle.secondary)
    async def optional(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You selected **Completed** as the task status.\nIs there anything you wish to change on the task details?",
                    view=ToChange(self.task_id, self.context, self.task_name, self.task_priority, "Completed", self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                    ephemeral=True
                    )


class ResolvedStatus(discord.ui.View):
    def __init__(self, task_id="", context="", task_name="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        super().__init__(timeout=180)

    @discord.ui.button(label="True", style=discord.ButtonStyle.danger)
    async def true(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You selected **True** as the resolved status.\nIs there anything you wish to change on the task details?",
                    view=ToChange(self.task_id, self.context, self.task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, "TRUE", self.deadline, self.notes),
                    ephemeral=True
                    )

    @discord.ui.button(label="False", style=discord.ButtonStyle.secondary)
    async def false(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You selected **False** as the resolved status.\nIs there anything you wish to change on the task details?",
                    view=ToChange(self.task_id, self.context, self.task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, "FALSE", self.deadline, self.notes),
                    ephemeral=True
                    )


class AnsweredNone(discord.ui.View):
    def __init__(self, task_id="", context="", task_name="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", change=False):
        self.task_id = task_id
        self.task_context = context
        self.task_name = task_name
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        super().__init__(timeout=180)


    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Please mention your Discord account as the creator of this task. Example: @YourName",
                ephemeral=True,
            )
        def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

        creator_mention_msg = await client.wait_for("message", check=check)
        creator_mention = creator_mention_msg.content.strip()
        await creator_mention_msg.delete() 

        await interaction.followup.send(
                "Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23",
                ephemeral=True,
            )
        respo_mentions_msg = await client.wait_for("message", check=check)
        respo_mentions = respo_mentions_msg.content.strip()
        await respo_mentions_msg.delete()

        result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range="Tickets!A:L"  # Adjust range to include Task ID and all details
            ).execute()

        rows = result.get("values", [])
        headers = rows[0]  # Assuming the first row contains column headers
        data_rows = rows[1:]  # Exclude the header row

        # Find the row with the given Task ID
        task_details = None
        for row in data_rows:
            if len(row) > 0 and row[0] == self.task_id:  # Ensure Task ID matches
                task_details = row
                break

        if task_details:
            # Task ID found, save details into variables
            (
                task_context_before,
                task_description_before,
                task_priority_before,
                task_status_before,
                requesting_committee_before,
                committee_responsible_before,
                subcommittee_responsible_before,
                receiving_committee_before,
                resolved_status_before,
                deadline_before,
                notes_before,
            ) = task_details[1:]  # Skip the Task ID (first column) 

        #task_description_before if type(self.task_name) != str else self.task_name
        #task_context_before if type(self.task_context) != str else self.task_context
        #task_priority_before if type(self.task_priority) != str else self.task_priority
        #task_status_before if type(self.task_status) != str else self.task_status
        #requesting_committee_before if type(self.requesting_committee) != str else self.requesting_committee
        #committee_responsible_before if type(self.committee_responsible) != str else self.committee_responsible
        #subcommittee_responsible_before if type(self.subcommittee_responsible) != str else self.subcommittee_responsible
        #receiving_committee_before if type(self.receiving_committee) != str else self.receiving_committee
        #resolved_status_before if type(self.resolved_status) != str else self.resolved_status
        #deadline_before if type(self.deadline) != str else self.deadline
        #notes_before if type(self.notes) != str else self.notes


        embed = discord.Embed(
                title="New Task Created!",
                description=(
                    f"**Task ID:** {self.task_id}\n"
                    f"**Task Name:** {task_description_before if type(self.task_name) != str else self.task_name}\n"
                    f"**Task Context:** {task_context_before if type(self.task_context) != str else self.task_context}\n"
                    f"**Task Priority:** {task_priority_before if type(self.task_priority) != str else self.task_priority}\n"
                    f"**Task Status:** {task_status_before if type(self.task_status) != str else self.task_status}\n"
                    f"**Requesting Committee:** {requesting_committee_before if type(self.requesting_committee) != str else self.requesting_committee}\n"
                    f"**Committee Responsible:** {committee_responsible_before if type(self.committee_responsible) != str else self.committee_responsible}\n"
                    f"**Subcommittee Responsible:** {subcommittee_responsible_before if type(self.subcommittee_responsible) != str else self.subcommittee_responsible}\n"
                    f"**Receiving Committee:** {receiving_committee_before if type(self.receiving_committee) != str else self.receiving_committee}\n"
                    f"**Task Resolved?** {resolved_status_before if type(self.resolved_status) != str else self.resolved_status}\n**"
                    f"**Due Date:** {deadline_before if type(self.deadline) != str else self.deadline}\n"
                    f"**Notes:** {notes_before if type(self.notes) != str else self.notes}\n"
                    f"**Task Creator:** {creator_mention}\n"
                    f"**Person/s in Charge:** {respo_mentions}"
                ),
                color=0xffcc1a,
            )
        await interaction.followup.send(embed=embed, ephemeral=True)

        # Send Embed to the other server
        target_guild = client.get_guild(1302238411020832780) #Server ID
        target_channel = target_guild.get_channel(1320416019272957993) #Text channel ID

        if target_channel:
            await target_channel.send(embed=embed)
        else:
            print('lala')


        update_task_in_google_sheets(self.task_id,[
            '',
            task_context_before if type(self.task_context) != str else self.task_context,
            task_description_before if type(self.task_name) != str else self.task_name,
            task_priority_before if type(self.task_priority) != str else self.task_priority,
            task_status_before if type(self.task_status) != str else self.task_status,
            requesting_committee_before if type(self.requesting_committee) != str else self.requesting_committee,
            committee_responsible_before if type(self.committee_responsible) != str else self.committee_responsible,
            subcommittee_responsible_before if type(self.subcommittee_responsible) != str else self.subcommittee_responsible,
            receiving_committee_before if type(self.receiving_committee) != str else self.receiving_committee,
            resolved_status_before if type(self.resolved_status) != str else self.resolved_status,
            deadline_before if type(self.deadline) != str else self.deadline,
            notes_before if type(self.notes) != str else self.notes,
        ])

        await interaction.followup.send(embed=embed, ephemeral=True)

        channel_id = 1302238822720868374  # Replace with your channel ID
        channel = client.get_channel(channel_id)

        embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button or modify tasks through the 'Edit Task' button.",
            color=0xffcc1a
        )
        embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
        
        view = MyView()

        time.sleep(2)

        await channel.send(embed=embed, view=view)

    @discord.ui.button(label="No", style=discord.ButtonStyle.secondary)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You selected **False** as the resolved status.\nIs there anything you wish to change on the task details?",
                    view=ToChange(self.task_id, self.context, self.task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, "FALSE", self.deadline, self.notes),
                    ephemeral=True
                    )


class ToChange(discord.ui.Select):
    def __init__(self, task_id, task_context, task_description, task_priority, task_status, requesting_committee, committee_responsible, subcommittee_responsible, receiving_committee, resolved_status, deadline, notes):
        self.task_id = task_id
        self.task_context = task_context
        self.task_description = task_description
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        #super().__init__(timeout=180)

        options = [
            discord.SelectOption(label="Task Context"),
            discord.SelectOption(label="Task Description"),
            discord.SelectOption(label="Task Priority"),
            discord.SelectOption(label="Task Status"),
            discord.SelectOption(label="Requesting Committee"),
            discord.SelectOption(label="Committee Responsible"),
            discord.SelectOption(label="Subcommittee Responsible"),
            discord.SelectOption(label="Receiving Committee"),
            discord.SelectOption(label="Resolved Status"),
            discord.SelectOption(label="Deadline"),
            discord.SelectOption(label="Notes"),
            discord.SelectOption(label="None"),

        ]
        super().__init__(placeholder=f"Is there any detail of task {task_id} you would like to be changed?", options=options, timeout=180)

    ##### add if else dito
    async def callback(self, interaction: discord.Interaction):
        selected_to_change = self.values[0]

        if selected_to_change == "Task Context":
            await interaction.response.send_message("You selected **Task Context** as the detail you wish to change.\nPlease select the **context** of the task:", view=TaskContext(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

        elif selected_to_change == "Task Description":
            await interaction.response.send_message("You selected **Task Description** as the detail you wish to change.\nPlease select the **description** of the task:", ephemeral=True)

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            task_name = msg.content
            await msg.delete() 

            await interaction.followup.send(
                f"You wrote {task_name} as the task description.\ns there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.task_context, task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                        ephemeral=True
            )

        elif selected_to_change == "Task Priority":
            await interaction.response.send_message("You selected **Priority** as the detail you wish to change.\nPlease select the **priority** of the task:", view=Priority(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

        elif selected_to_change == "Task Status":
            await interaction.response.send_message("You selected **Status** as the detail you wish to change.\nPlease select the **status** of the task:", view=Status(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

        elif selected_to_change == "Requesting Committee":
            await interaction.response.send_message("You selected **Requesting Committee** as the detail you wish to change.\nPlease select the **committee requesting** for the task:", view=RequestingCommittee(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

        elif selected_to_change == "Committee Responsible":
            await interaction.response.send_message("You selected **Committee Responsible** as the detail you wish to change.\nPlease select the **committee responsible** for the task:", view=CommitteeResponsible(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

        elif selected_to_change == "Subcommittee Responsible":
            if self.committee_responsible == "SB":
                await interaction.response.send_message(
                    "You selected **Subcommittee Responsible** as the detail you wish to change.\nPlease select the **subcommittee responsible** for the task:",
                    view=SubcommitteeResponsibleSB(
                        self.task_id, self.task_context, self.task_description, self.task_priority,
                        self.task_status, self.requesting_committee, self.committee_responsible,
                        self.subcommittee_responsible, self.receiving_committee, self.resolved_status,
                        self.deadline, self.notes, True
                    ),
                    ephemeral=True
                )
            elif self.committee_responsible == "CM":
                await interaction.response.send_message(
                    "You selected **Subcommittee Responsible** as the detail you wish to change.\nPlease select the **subcommittee responsible** for the task:",
                    view=SubcommitteeResponsibleCM(
                        self.task_id, self.task_context, self.task_description, self.task_priority,
                        self.task_status, self.requesting_committee, self.committee_responsible,
                        self.subcommittee_responsible, self.receiving_committee, self.resolved_status,
                        self.deadline, self.notes, True
                    ),
                    ephemeral=True
                )
            elif self.committee_responsible == "CX":
                await interaction.response.send_message(
                    "You selected **Subcommittee Responsible** as the detail you wish to change.\nPlease select the **subcommittee responsible** for the task:",
                    view=SubcommitteeResponsibleCX(
                        self.task_id, self.task_context, self.task_description, self.task_priority,
                        self.task_status, self.requesting_committee, self.committee_responsible,
                        self.subcommittee_responsible, self.receiving_committee, self.resolved_status,
                        self.deadline, self.notes, True
                    ),
                    ephemeral=True
                )
            elif self.committee_responsible == "HR":
                await interaction.response.send_message(
                    "You selected **Subcommittee Responsible** as the detail you wish to change.\nPlease select the **subcommittee responsible** for the task:",
                    view=SubcommitteeResponsibleHR(
                        self.task_id, self.task_context, self.task_description, self.task_priority,
                        self.task_status, self.requesting_committee, self.committee_responsible,
                        self.subcommittee_responsible, self.receiving_committee, self.resolved_status,
                        self.deadline, self.notes, True
                    ),
                    ephemeral=True
                )
            elif self.committee_responsible == "IT":
                await interaction.response.send_message(
                    "You selected **Subcommittee Responsible** as the detail you wish to change.\nPlease select the **subcommittee responsible** for the task:",
                    view=SubcommitteeResponsibleIT(
                        self.task_id, self.task_context, self.task_description, self.task_priority,
                        self.task_status, self.requesting_committee, self.committee_responsible,
                        self.subcommittee_responsible, self.receiving_committee, self.resolved_status,
                        self.deadline, self.notes, True
                    ),
                    ephemeral=True
                )
            elif self.committee_responsible == "MK":
                await interaction.response.send_message(
                    "You selected **Subcommittee Responsible** as the detail you wish to change.\nPlease select the **subcommittee responsible** for the task:",
                    view=SubcommitteeResponsibleMK(
                        self.task_id, self.task_context, self.task_description, self.task_priority,
                        self.task_status, self.requesting_committee, self.committee_responsible,
                        self.subcommittee_responsible, self.receiving_committee, self.resolved_status,
                        self.deadline, self.notes, True
                    ),
                    ephemeral=True
                )
            elif self.committee_responsible == "FS":
                await interaction.response.send_message(
                    "You selected **Subcommittee Responsible** as the detail you wish to change.\nPlease select the **subcommittee responsible** for the task:",
                    view=SubcommitteeResponsibleFS(
                        self.task_id, self.task_context, self.task_description, self.task_priority,
                        self.task_status, self.requesting_committee, self.committee_responsible,
                        self.subcommittee_responsible, self.receiving_committee, self.resolved_status,
                        self.deadline, self.notes, True
                    ),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"Invalid committee responsible: {self.committee_responsible}",
                    ephemeral=True
                )


        elif selected_to_change == "Receiving Committee":
            await interaction.response.send_message("You selected **Receiving Committee** as the detail you wish to change.\nPlease select the **committee receiving** the output of the task:", view=ReceivingCommittee(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

        elif selected_to_change == "Resolved Status":
            await interaction.response.send_message("You selected **Resolved Status** as the detail you wish to change.\nPlease select the **resolved status** of the task.\nTRUE if resolved, FALSE if otherwise.", view=ResolvedStatus(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

        elif selected_to_change == "Deadline":
            await interaction.response.send_message("You selected **Deadline** as the detail you wish to change.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM", ephemeral=True)

            def check(msg):
                    return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            deadline = msg.content
            await msg.delete() 

            await interaction.followup.send(
                f"You wrote {deadline} as the task deadline.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.task_context, self.task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, deadline, self.notes),
                        ephemeral=True
            )

        elif selected_to_change == "Notes":
            await interaction.response.send_message("You selected **Notes** as the detail you wish to change.\nPlease type the things you wish to be noted about the task.", ephemeral=True)

            def check(msg):
                    return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            notes = msg.content
            await msg.delete() 

            await interaction.followup.send(
                f"You wrote {notes} as the notes for the task.\nIs there anything you wish to change on the task details?",
                        view=ToChange(self.task_id, self.task_context, self.task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, notes),
                        ephemeral=True
            )

        elif selected_to_change == "None":
            await interaction.response.send_message("You selected **None** as the detail you wish to change.\n", view=AnsweredNone(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

        #### insert embed

            await interaction.response.send_message("Select \'Yes\' if the details here are correct, \'No\' if not.\n", view=AnsweredNone(self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, True), ephemeral=True)

#
client.run(BOTTOKEN)
#
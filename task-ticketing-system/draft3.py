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
        print("Data to be appended:", data)
        print("Append response:", result)
        print(f"{result.get('updates').get('updatedRows')} row/s appended.")
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

async def show_embed():
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


@client.event
async def on_ready():
    await show_embed()  # Call the show_embed function with await


# Custom view for interactive buttons and dropdown
class MyView(discord.ui.View):
    @discord.ui.button(label="Create Task", style=discord.ButtonStyle.primary)
    async def create_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show the dropdown menu first
        await interaction.response.send_message("Select the context of the task:", view=DropdownView("","","", "task_context"), ephemeral=True)

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

class TaskContextDropdown(discord.ui.Select):
    def __init__(self): 
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
        await interaction.response.send_message(
            f"Please type your task description in the chatbox below.",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        # Wait for the user to input the task description
        msg = await client.wait_for("message", check=check)
        task_name = msg.content  # Extract the task description
        await interaction.followup.send(
            "Select the priority of the task:",
            view=DropdownView(context=selected_context, task_name=task_name, section="priority"),
            ephemeral=True
        )


class TaskPriorityDropdown(discord.ui.Select):
    def __init__(self, context, task_name):
        self.context = context
        self.task_name = task_name
        options = [
            discord.SelectOption(label="P0 - Critical"),  # you may add description = ""
            discord.SelectOption(label="P1 - High"),
            discord.SelectOption(label="P2 - Moderate"),
            discord.SelectOption(label="P3 - Low"),
            discord.SelectOption(label="P4 - Optional"),
        ]
        super().__init__(placeholder="Select the priority of the task...", options=options)

    ##### add if else dito
    async def callback(self, interaction: discord.Interaction):
        selected_priority = self.values[0]  # Get the selected context
        #await interaction.response.send_message("Select the context of the task:", view=DropdownView("","","", "task_context"), ephemeral=True)
        await interaction.response.send_message("Select the committee requesting for the task:", view=DropdownView(self.context, self.task_name, selected_priority, "requesting_committee"), ephemeral=True)

class CommitteeDropdown(discord.ui.Select):
    def __init__(self, context, task_name, priority, label, requesting_committee="", committee_responsible="", subcommittee="", receiving_committee=""):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.label = label
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee = subcommittee
        self.receiving_committee = receiving_committee

        options = [
            discord.SelectOption(label="SB"),
            discord.SelectOption(label="CM"),
            discord.SelectOption(label="CX"),
            discord.SelectOption(label="HR"),
            discord.SelectOption(label="IT"),
            discord.SelectOption(label="MK"),
            discord.SelectOption(label="FS"),
        ]
        if self.label == "requesting_committee":
            super().__init__(placeholder="Select the committee requesting the task...", options=options)
        elif self.label == "committee_responsible":
            super().__init__(placeholder="Select the committee assigned or responsible for the task...", options=options)
        elif self.label == "receiving_committee":
            super().__init__(placeholder="Select the committee receiving the output of the task", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.label == "requesting_committee":
            sel_requesting_committee = self.values[0]
            await interaction.response.send_message(
                "Select the committee assigned or responsible for the task:",
                view=DropdownView(
                    context=self.context,
                    task_name=self.task_name,
                    priority=self.priority,
                    section="committee_responsible",
                    requesting_committee=sel_requesting_committee,
                ),
                ephemeral=True,
            )

        elif self.label == "committee_responsible":
            committee_responsible = self.values[0]
            await interaction.response.send_message(
                "Select the subcommittee assigned or responsible for the task:",
                view=DropdownView(
                    context=self.context,
                    task_name=self.task_name,
                    priority=self.priority,
                    section="subcommittee_responsible",
                    requesting_committee=self.requesting_committee,
                    committee_responsible=committee_responsible,
                ),
                ephemeral=True,
            )

        elif self.label == "receiving_committee":
            selected_receiving_committee = self.values[0]
            await interaction.response.send_message(
                "Please type the deadline for the task in this format:\nMM/DD/YYYY HH:MM",
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
                    f"**Subcommittee Responsible:** {self.subcommittee}\n"
                    f"**Receiving Committee:** {selected_receiving_committee}\n"
                    f"**Due Date:** {deadline}\n"
                    f"**Notes:** {notes}"
                ),
                color=0xffcc1a,
            )
            
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
                self.subcommittee,
                selected_receiving_committee,
                "",
                deadline,
                notes,
            ])


            await interaction.followup.send(embed=embed, ephemeral=True)  # Changed from send_message to send

            channel_id = 1302238822720868374  # Replace with your channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the 'Create Task' button\nor modify tasks through the 'Edit Task' button.",
            color=0xffcc1a
            )
            
            view = MyView()

            time.sleep(0.3)
            # Send the embed with buttons
            await channel.send(embed = embed, view=view)


class SubcommitteeDropdown(discord.ui.Select):
    def __init__(self, context, task_name, priority, label, requesting_committee, committee_responsible, subcommittee, receiving_committee):
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.label = label
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee = subcommittee
        self.receiving_committee = receiving_committee

        print(f"committee_responsible: {committee_responsible}")  # Debugging


        # Define options based on the committee responsible
        options = []
        if committee_responsible == "SB":
            options = [
                discord.SelectOption(label="President (SB)"),
                discord.SelectOption(label="Executive Vice President (SB)"),
                discord.SelectOption(label="Process Excellence (SB)"),
                discord.SelectOption(label="University Affairs (SB)")
            ]
        elif committee_responsible == "CM":
            options = [
                discord.SelectOption(label="Vice President (CM)"),
                discord.SelectOption(label="Brand Management (CM)"),
                discord.SelectOption(label="External Communications (CM)")
            ]
        elif committee_responsible == "CX":
            options = [
                discord.SelectOption(label="Vice President (CX)"),
                discord.SelectOption(label="Customer Development (CX)"),
                discord.SelectOption(label="Sales (CX)")
            ]
        elif committee_responsible == "HR":
            options = [
                discord.SelectOption(label="Vice President (HR)"),
                discord.SelectOption(label="Performance Management (HR)"),
                discord.SelectOption(label="Membership (HR)"),
                discord.SelectOption(label="Organization Management (HR)")
            ]
        elif committee_responsible == "IT":
            options = [
                discord.SelectOption(label="Vice President (IT)"),
                discord.SelectOption(label="Web Development (IT)"),
                discord.SelectOption(label="Information Systems (IT)"),
                discord.SelectOption(label="Automation (IT)")
            ]
        elif committee_responsible == "MK":
            options = [
                discord.SelectOption(label="Vice President (MK)"),
                discord.SelectOption(label="External Relations (MK)"),
                discord.SelectOption(label="Marketing Operations (MK)")
            ]
        elif committee_responsible == "FS":
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

        selected_subcommittee = self.values[0]  # Get the selected subcommittee

        print(f"selected_subcommittee: {selected_subcommittee}")  # Debugging


        # Transition to the receiving committee dropdown
        await interaction.response.send_message(
            "Select the committee receiving the output of the task:",
            view=DropdownView(
                context=self.context,
                task_name=self.task_name,
                priority=self.priority,
                section="receiving_committee",
                requesting_committee=self.requesting_committee,
                committee_responsible=self.committee_responsible,
                subcommittee=selected_subcommittee,
            ),
            ephemeral=True,
        )


# Dropdown view for task context
class DropdownView(discord.ui.View):
    def __init__(self, context = "", task_name = "", priority = "", section = "", requesting_committee = "", committee_responsible = "", subcommittee = "", receiving_committee = ""):
        super().__init__()
        if section == "task_context":
            self.add_item(TaskContextDropdown())
        elif section == "priority":
            self.add_item(TaskPriorityDropdown(context, task_name))
        elif section in ("requesting_committee", "committee_responsible", "receiving_committee"):
            self.add_item(CommitteeDropdown(context, task_name, priority, section, requesting_committee, committee_responsible, subcommittee, receiving_committee))
        elif section == "subcommittee_responsible":
            self.add_item(SubcommitteeDropdown(context, task_name, priority, section, requesting_committee, committee_responsible, subcommittee, receiving_committee))


class ToChange(discord.ui.View):
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
        super().__init__(timeout=180)

client.run(BOTTOKEN)  # Replace BOTTOKEN with your actual bot token

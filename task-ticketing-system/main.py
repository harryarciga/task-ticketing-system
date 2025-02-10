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
        await interaction.response.send_message("Select the context of the task:", view=DropdownView("task_context","","",""), ephemeral=True)

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
                        view=DropdownView("to_change", task_id, task_context, task_description, task_priority, task_status, requesting_committee, committee_responsible, subcommittee_responsible, receiving_committee, resolved_status, deadline, notes),
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
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""): 
        self.task_id = task_id
        self.task_context = task_context
        self.task_name = task_description
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
        if self.change == "yes":
            await interaction.response.defer(ephemeral=True)
            
            await interaction.followup.send(
                f"You have selected {selected_context} as your context. ",
                view=DropdownView("to_change", self.task_id, selected_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

            
        else:
            await interaction.response.send_message(
                f"Please type your task description in the chatbox below.",
                ephemeral=True
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            # Wait for the user to input the task description
            msg = await client.wait_for("message", check=check)
            task_name = msg.content  # Extract the task description
            await msg.delete() 

            await interaction.followup.send(
                "Select the priority of the task:",
                view=DropdownView(section="priority", context=selected_context, task_name=task_name),
                ephemeral=True
            )


class TaskPriorityDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""):
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
        selected_priority = self.values[0]
        if self.change == "yes":
            await interaction.response.defer(ephemeral=True)

            await interaction.followup.send(
                f"You have selected {selected_priority} as your task_priority.",
                view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, selected_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            await interaction.response.send_message("Select the committee requesting for the task:", view=DropdownView("requesting_committee", context=self.task_context, task_name=self.task_description, priority=selected_priority), ephemeral=True)


class CommitteeDropdown(discord.ui.Select):
    def __init__(self, change="", label="", task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""):
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
        self.label = label

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
            if self.change == "yes":
                await interaction.response.defer(ephemeral=True)

                await interaction.followup.send(
                f"You have selected {sel_requesting_committee} as the committee requesting the task.",
                view=DropdownView("to_change", self.task_id, self.context, self.task_name, self.priority, self.task_status, sel_requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
                )

            else:
                await interaction.response.send_message(
                    "Select the committee assigned or responsible for the task:",
                    view=DropdownView(
                        section="committee_responsible",
                        context=self.context,
                        task_name=self.task_name,
                        priority=self.priority,
                        requesting_committee=sel_requesting_committee,
                    ),
                    ephemeral=True,
                )

        elif self.label == "committee_responsible":
            committee_responsible = self.values[0]
            if self.change == "yes":
                await interaction.response.defer(ephemeral=True)

                await interaction.followup.send(
                f"You have selected {committee_responsible} as the committee assigned to do the task.",
                view=DropdownView("to_change", self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
                )

            else:
                await interaction.response.send_message(
                    "Select the subcommittee assigned or responsible for the task:",
                    view=DropdownView(
                        section="subcommittee_responsible",
                        context=self.context,
                        task_name=self.task_name,
                        priority=self.priority,
                        requesting_committee=self.requesting_committee,
                        committee_responsible=committee_responsible,
                    ),
                    ephemeral=True,
                )

        elif self.label == "receiving_committee":
            selected_receiving_committee = self.values[0]
            if self.change == "yes":
                await interaction.response.defer(ephemeral=True)

                await interaction.followup.send(
                f"You have selected {selected_receiving_committee} as the committee receiving the output of the task.",
                view=DropdownView("to_change", self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, selected_receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
                )

            else:
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
                        f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                        f"**Receiving Committee:** {selected_receiving_committee}\n"
                        f"**Due Date:** {deadline}\n"
                        f"**Notes:** {notes}"
                    ),
                    color=0xffcc1a,
                )
                print(f"**Task ID:** 2425-00011\n"
                        f"**Task Name:** {self.task_name}\n"
                        f"**Task Context:** {self.context}\n"
                        f"**Task Priority:** {self.priority}\n"
                        f"**Requesting Committee:** {self.requesting_committee}\n"
                        f"**Committee Responsible:** {self.committee_responsible}\n"
                        f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                        f"**Receiving Committee:** {selected_receiving_committee}\n"
                        f"**Due Date:** {deadline}\n"
                        f"**Notes:** {notes}"




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
                    self.subcommittee_responsible,
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
    def __init__(self, label="", change="", task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""):
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
        selected_subcommittee = self.values[0]
        if self.change == "yes":
            await interaction.response.defer(ephemeral=True)

            await interaction.followup.send(
                f"You have selected {selected_subcommittee} as the subcommittee assigned or responsible for the task.",
                view=DropdownView("to_change", self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        else:
            # Transition to the receiving committee dropdown
            await interaction.response.send_message(
                "Select the committee receiving the output of the task:",
                view=DropdownView(
                    section="receiving_committee",
                    context=self.context,
                    task_name=self.task_name,
                    priority=self.priority,
                    requesting_committee=self.requesting_committee,
                    committee_responsible=self.committee_responsible,
                    subcommittee_responsible=selected_subcommittee,
                ),
                ephemeral=True,
            )


class TaskStatusDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""):
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

        options = [
            discord.SelectOption(label="Acknowledged"),  # you may add description = ""
            discord.SelectOption(label="In Progress"),
            discord.SelectOption(label="Blocked"),
            discord.SelectOption(label="Completed")
        ]
        super().__init__(placeholder="Select the status of the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_task_status = self.values[0]
        await interaction.followup.send(
            f"You have selected {selected_task_status} as your task status.",
            view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, selected_task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
            ephemeral=True
            )


class ResolvedStatusDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""):
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

        options = [
            discord.SelectOption(label="True"),  # you may add description = ""
            discord.SelectOption(label="False")
        ]
        super().__init__(placeholder="Select True if the task has been resolved, False if otherwise.", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_resolved_status = self.values[0]
        if selected_resolved_status == "True":
            await interaction.followup.send(
            f"You have selected {selected_resolved_status} as the resolved status of the task.",
            view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, "TRUE", self.deadline, self.notes),
            ephemeral=True
            )
        else:
            await interaction.followup.send(
            f"You have selected {selected_resolved_status} as the resolved status of the task.",
            view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, "FALSE", self.deadline, self.notes),
            ephemeral=True
            )


class AnsweredNoneDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""):
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

        options = [
            discord.SelectOption(label="Yes"),  # you may add description = ""
            discord.SelectOption(label="No")
        ]
        super().__init__(placeholder="Select Yes if the task has been resolved, No if otherwise.", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_resolved_status = self.values[0]
        if selected_resolved_status == "Yes":
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
                        f"**Task Name:** {task_description_before if type(self.task_description) != str else self.task_description}\n"
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
                task_description_before if type(self.task_description) != str else self.task_description,
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





        else:
            await interaction.followup.send(
            f"It seems like you still want to change some details.",
            view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
            ephemeral=True
            )



# Dropdown view for task context
class DropdownView(discord.ui.View):
    def __init__(self, section="", task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""):
        super().__init__()

        if section == "task_context":
            self.add_item(TaskContextDropdown())
        elif section == "priority":
            self.add_item(TaskPriorityDropdown(task_context=context, task_description=task_name))
        elif section in ("requesting_committee", "committee_responsible", "receiving_committee"):
            self.add_item(CommitteeDropdown(label=section, context=context, task_name=task_name, priority=priority, requesting_committee=requesting_committee, committee_responsible=committee_responsible, subcommittee_responsible=subcommittee_responsible, receiving_committee=receiving_committee))
        elif section == "subcommittee_responsible":
            self.add_item(SubcommitteeDropdown(label=section, context=context, task_name=task_name, priority=priority, requesting_committee=requesting_committee, committee_responsible=committee_responsible, subcommittee_responsible=subcommittee_responsible, receiving_committee=receiving_committee))
        elif section == "to_change":
            self.add_item(ToChangeDropdown(task_id=task_id, task_context=context, task_description=task_name, task_priority=priority, task_status=task_status, requesting_committee=requesting_committee, committee_responsible=committee_responsible, subcommittee_responsible=subcommittee_responsible, receiving_committee=receiving_committee, resolved_status=resolved_status, deadline=deadline, notes=notes))

class ToChangeDropdown(discord.ui.Select):
    def __init__(self, task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes=""):
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
        #self.change = change

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
        super().__init__(placeholder=f"Is there any detail of task {task_id} you would like to be changed?", options=options)

    ##### add if else dito
    async def callback(self, interaction: discord.Interaction):
        selected_to_change = self.values[0]
        if selected_to_change == "Task Context":
            await interaction.response.defer(ephemeral=True)
            
            # Create the view
            view = discord.ui.View()
            view.add_item(TaskContextDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))
            
            # Now use followup
            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,
                ephemeral=True
            )          

        elif selected_to_change == "Task Description":
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
                f"You wrote {task_name} as your task description",
                view=DropdownView("to_change", self.task_id, self.task_context, task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes),
                ephemeral=True
            )

        elif selected_to_change == "Task Priority":
            await interaction.response.defer(ephemeral=True)

            view = discord.ui.View()
            view.add_item(TaskPriorityDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))

            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,  
                ephemeral=True
            )


        elif selected_to_change == "Task Status":
            await interaction.response.defer(ephemeral=True)
            
            # Create the view
            view = discord.ui.View()
            view.add_item(TaskStatusDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))
            
            # Now use followup
            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,
                ephemeral=True
            )  

        elif selected_to_change == "Requesting Committee":
            await interaction.response.defer(ephemeral=True)
            
            # Create the view
            view = discord.ui.View()
            view.add_item(CommitteeDropdown("yes", "requesting_committee", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))            
            
            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,
                ephemeral=True
            )  

        elif selected_to_change == "Committee Responsible":
            await interaction.response.defer(ephemeral=True)
            
            # Create the view
            view = discord.ui.View()
            view.add_item(CommitteeDropdown("yes", "committee_responsible", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))
            
            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,
                ephemeral=True
            )  
            
        elif selected_to_change == "Subcommittee Responsible":
            await interaction.response.defer(ephemeral=True)
            
            # Create the view
            view = discord.ui.View()
            view.add_item(SubcommitteeDropdown("yes", "", "subcommittee_responsible", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))
            
            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,
                ephemeral=True
            )  



        elif selected_to_change == "Receiving Committee":
            await interaction.response.defer(ephemeral=True)
            
            # Create the view
            view = discord.ui.View()
            view.add_item(CommitteeDropdown("yes", "receiving_committee", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))
            
            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,
                ephemeral=True
            )  
            
        elif selected_to_change == "Resolved Status":
            await interaction.response.defer(ephemeral=True)
            
            # Create the view
            view = discord.ui.View()
            view.add_item(ResolvedStatusDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))
            
            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,
                ephemeral=True
            )  


        elif selected_to_change == "Deadline":
            await interaction.response.send_message("You selected **Deadline** as the detail you wish to change.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM", ephemeral=True)

            def check(msg):
                    return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            deadline = msg.content
            await msg.delete() 

            await interaction.followup.send(
                f"You wrote {deadline} as your task deadline.",
                view=DropdownView("to_change", self.task_id, self.task_context, self.task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, deadline, self.notes),
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
                f"You wrote \"{notes}\" as the things you wish to be noted about the task.",
                view=DropdownView("to_change", self.task_id, self.task_context, self.task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, notes),
                ephemeral=True
            )
            
        elif selected_to_change == "None":
            # First, acknowledge the interaction to prevent timeout
            await interaction.response.defer(ephemeral=True)
            
            # Create the view
            view = discord.ui.View()
            view.add_item(AnsweredNoneDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes))
            
            # Now use followup
            await interaction.followup.send(
                f"You have selected {selected_to_change} as the detail you would like to change.",
                view=view,
                ephemeral=True
            )                    



client.run(BOTTOKEN)  # Replace BOTTOKEN with your actual bot token

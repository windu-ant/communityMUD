"""
Custom unloggedin commands

This module contains custom versions of the commands for unloggedin users,
particularly modifying the account creation process to include Terms of Service
and Code of Conduct confirmation.

This works for the connect/create command style login but not the username/password prompt style login.
"""

import re
from django.conf import settings
from evennia.utils import class_from_module
from evennia.commands.default.unloggedin import CmdUnconnectedCreate as DefaultCmdUnconnectedCreate

class CmdUnconnectedCreate(DefaultCmdUnconnectedCreate):
    """
    create a new account account

    Usage (at login screen):
      create <accountname> <password>
      create "account name" "pass word"

    This creates a new account account. You will be asked to agree to the
    Terms of Service and Code of Conduct during the creation process.

    If you have spaces in your name, enclose it in double quotes.
    """

    key = "create"
    aliases = ["cre", "cr"]
    locks = "cmd:all()"
    arg_regex = r"\s.*?|$"

    def func(self):
        """Do checks and create account, with ToS and CoC confirmation"""

        session = self.caller
        args = self.args.strip()

        address = session.address

        # Get account class
        Account = class_from_module(settings.BASE_ACCOUNT_TYPECLASS)

        # extract double quoted parts
        parts = [part.strip() for part in re.split(r"\"", args) if part.strip()]
        if len(parts) == 1:
            # this was (hopefully) due to no quotes being found
            parts = parts[0].split(None, 1)
        if len(parts) != 2:
            string = (
                "\n Usage (without <>): create <n> <password>"
                "\nIf <n> or <password> contains spaces, enclose it in double quotes."
            )
            session.msg(string)
            return

        username, password = parts

        # pre-normalize username so the user know what they get
        non_normalized_username = username
        username = Account.normalize_username(username)
        if non_normalized_username != username:
            session.msg(
                "Note: your username was normalized to strip spaces and remove characters "
                "that could be visually confusing."
            )

        # have the user verify their new account was what they intended
        answer = yield (
            f"You want to create an account '{username}' with password '{password}'."
            "\nIs this what you intended? [Y]/N?"
        )
        if answer.lower() in ("n", "no"):
            session.msg("Aborted. If your user name contains spaces, surround it by quotes.")
            return

        # Present Terms of Service and Code of Conduct
        tos_text = """
|y==============================================================|n
|rTERMS OF SERVICE|n

By creating an account, you agree to:

1. Respect all users and staff
2. Follow all game rules and policies
3. Not exploit bugs or game mechanics
4. Not engage in harassment or abuse
5. Allow your account data to be stored

This is a placeholder for the full Terms of Service, which will be 
available later.

|y==============================================================|n
"""
        coc_text = """
|y==============================================================|n
|rCODE OF CONDUCT|n

As a player, you will:

1. Be respectful of other players
2. Use appropriate language
3. Not engage in discrimination or harassment
4. Respect the privacy of other players
5. Follow staff instructions

This is a placeholder for the full Code of Conduct, which will be 
available later.

|y==============================================================|n
"""
        session.msg(tos_text)
        session.msg(coc_text)
        
        # Ask for confirmation
        tos_answer = yield "Do you agree to the Terms of Service and Code of Conduct? (yes/no)"
        if tos_answer.lower() not in ("yes", "y"):
            session.msg("You must agree to the Terms of Service and Code of Conduct to create an account.")
            return

        # everything's ok. Create the new player account.
        account, errors = Account.create(
            username=username, password=password, ip=address, session=session
        )
        if account:
            # tell the caller everything went well.
            string = "A new account '%s' was created. Welcome!"
            if " " in username:
                string += (
                    "\n\nYou can now log in with the command 'connect \"%s\" <your password>'."
                )
            else:
                string += "\n\nYou can now log with the command 'connect %s <your password>'."
            session.msg(string % (username, username))
        else:
            session.msg("|R%s|n" % "\n".join(errors)) 
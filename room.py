import dataset
from datetime import datetime, timedelta
import discord

# Start database
db = dataset.connect('sqlite:///:memory:')
rooms = db.get_table('rooms', primary_id='role_id')

class Room:
    def __init__(self, role_id, guild, activity, description, created, timeout, players, host, waiting_for):
        self.role_id = role_id
        self.guild = guild
        self.activity = activity
        self.description = description
        self.created = created
        self.timeout = timeout
        self.players = players
        self.host = host
        self.waiting_for = waiting_for

        rooms.upsert(dict(
            role_id=role_id,
            guild=guild,
            activity=activity,
            description=description,
            created=created,
            timeout=timeout,
            players='\\'.join(players),
            host=host,
            waiting_for=waiting_for ), ['role_id'])
            
    @classmethod
    def from_message(cls, activity, ctx, args, role_id):
        """Create a Room from a message"""
        # role_id = role_id
        guild = ctx.message.guild.id
        # activity = activity
        description = args[1] if len(args) > 1 else ''
        created = datetime.now()
        timeout = 60 * 60
        players = []
        host = ctx.message.author.name
        waiting_for = 2
        return cls(role_id, guild, activity, description, created, timeout, players, host, waiting_for)
            
    @classmethod
    def from_query(cls, data):
        """Create a Room from a query"""
        role_id = data['role_id']
        guild = data['guild']
        activity = data['activity']
        description = data['description']
        created = data['created']
        timeout = data['timeout']
        players = data['players'].split('\\')
        host = data['host']
        waiting_for = data['waiting_for']
        return cls(role_id, guild, activity, description, created, timeout, players, host, waiting_for)

    def get_embed(self):
        """Generate a discord.Embed for this room"""
        description = discord.Embed.Empty if self.description == '' else self.description
        # TODO: format time
        remaining_time = self.created + timedelta(seconds=self.timeout) - datetime.now()

        embed = discord.Embed(
            color=discord.Color.blue(),
            description=description,
            timestamp=self.created,
            title=self.activity )
        embed.add_field(
            name="Players ({0})".format(len(self.players)),
            value=", ".join(self.players) )
        embed.add_field(
            name="Waiting for {0} players".format(self.waiting_for),
            value="Room will disband in {0}".format(remaining_time) )
        embed.set_footer(
            text="Host: {0}".format(self.host),
            icon_url=discord.Embed.Empty )
        
        return embed

    async def add_player(self, player):
        """Add a player to this room"""
        if player.name not in self.players:
            role = discord.utils.get(player.guild.roles, id=self.role_id)
            await player.add_roles(role)

            self.players.append(player.name)
            rooms.update(dict(role_id=self.role_id, players='\\'.join(self.players)), ['role_id'])
            return True
        return False

    async def remove_player(self, player):
        """Remove a player from this room"""
        if player.name in self.players:
            role = discord.utils.get(player.guild.roles, id=self.role_id)
            await player.remove_roles(role)
            self.players.remove(player.name)
            rooms.update(dict(role_id=self.role_id, players='\\'.join(self.players)), ['role_id'])
            return True
        return False

    def disband(self):
        """Delete room"""
        rooms.delete(role_id=self.role_id)
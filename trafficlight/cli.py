import click


@click.group()
def cli():
    pass


@click.command()
@click.argument("message")
def show(message: str):
    from rich import print
    from thefuzz import process

    from trafficlight import protos
    from trafficlight.proto_utils.proto_format import MessageFormatter

    message_map = {**protos.DESCRIPTOR.message_types_by_name, **protos.DESCRIPTOR.enum_types_by_name}

    result = process.extractOne(message, message_map.keys())
    message = message_map[result[0]]

    formatter = MessageFormatter(type_emphasize=True)
    print(formatter.format_message_type(message))


@click.command()
def run():
    from trafficlight.trafficlight import run as start_tl
    start_tl()


cli.add_command(show)
cli.add_command(run)

from pathlib import Path
import json
import time

import click

from stegl.processlaunching import ProcessCapture, ExternalGame
from stegl import configurationui
from stegl import logging as stegl_logging
from stegl.logging import print_log


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None or ctx.invoked_subcommand == "setup_game":
        ctx.forward(setup_game)
    elif ctx.invoked_subcommand == "launch_external_game":
        ctx.forward(launch_external_game)


@cli.command()
@click.argument("configuration")
@click.option("--slient", is_flag=True, default=False, help="Supresses all console outputs.")
def launch_external_game(configuration, slient):
    """Invokes the external game with its dependencies (e.g. launchers).
    
    For CONFIGURATION, a path to a configuration .stegl-file is expected."""
    
    stegl_logging.ACTIVE = not slient

    try:
        config_path = Path(configuration)
        del configuration

        if not config_path.exists():
            raise ValueError("Configuration does not exist")
        
        with config_path.open() as f:
            config = json.load(f)

        game_starter = ProcessCapture(**config["GAME"]["launch_config"])
        dependencies = [ProcessCapture(**dep_config) for dep_config in config["DEPENDENCIES"]]

        externalGame = ExternalGame(
            game_search_paths=config["GAME"]["game_search_paths"],
            game_starter=game_starter, 
            dependencies=dependencies,
            game_search_timeout=config["GAME"]["game_search_timeout"],
            after_game_wait=config["GAME"]["after_game_wait"]
        )

        launch_art = """
Launched using:

   ██████╗  ████████╗  ███████╗   ██████╗   ██╗
  ██╔════╝░░╚══██╔══╝░░██╔════╝░░██╔════╝░░░██║░░░
  ╚█████╗░░░░░░██║░░░░░█████╗░░░░██║░░██╗░░░██║░░░
   ╚═══██╗░░░░░██║░░░░░██╔══╝░░░░██║░░╚██╗░░██║░░░
  ██████╔╝░░░░░██║░░░░░███████╗░░╚██████╔╝░░███████╗
  ╚═════╝      ╚═╝     ╚══════╝   ╚═════╝   ╚══════╝
  (Steam External Game Launcher)

"""
        print_log(launch_art)
        externalGame.run()
        time.sleep(2)
    except Exception as e:
        print_log(f"An error occured: {repr(e)}")
        print_log(f"Trying to terminate game processes.")
        externalGame.terminate()
        time.sleep(2)
        exit(1)


@cli.command()
def setup_game():
    """(Default) Launches UI to create a configuration for a game."""
    configurationui.launch()


if __name__ == '__main__':
    cli()
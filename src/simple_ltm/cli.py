#!/usr/bin/env python3
"""
cli.py
======

A polished command-line chatbot interface with long-term memory.
"""

import os
import sys
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich.table import Table
from rich import box

from .agent import MemoryAgent
from .memory import LongTermMemory


class MemoryChatCLI:
    """Rich command-line interface for the memory chatbot."""
    
    def __init__(self):
        self.console = Console()
        self.agent: Optional[MemoryAgent] = None
        self.user_id: Optional[str] = None
        self.memory_store = LongTermMemory()
        
    def display_banner(self):
        """Display welcome banner."""
        banner = """
╔══════════════════════════════════════════════════════════╗
║           🧠 Long-Term Memory Chatbot 🧠                  ║
╚══════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan", justify="center")
        self.console.print(
            "A conversational AI that remembers you across sessions\n",
            style="italic",
            justify="center"
        )
    
    def select_or_create_user(self) -> str:
        """User selection/creation interface."""
        self.console.print(Panel.fit(
            "👤 User Selection",
            style="bold yellow"
        ))
        
        # Get existing users
        users = self.memory_store.list_users()
        
        if users:
            # Display existing users
            table = Table(title="Existing Users", box=box.ROUNDED)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("User", style="green")
            table.add_column("Memory Preview", style="dim")
            
            for i, user in enumerate(users, 1):
                memory = self.memory_store.read(user)
                preview = memory[:50] + "..." if len(memory) > 50 else memory
                table.add_row(str(i), user, preview)
            
            self.console.print(table)
            self.console.print()
            
            # Prompt for selection
            choice = Prompt.ask(
                "Enter a number to select a user, or type a new username",
                default="new"
            )
            
            # Check if numeric selection
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(users):
                    return users[idx]
            except ValueError:
                pass
            
            # Otherwise treat as new username
            return choice
        else:
            # No existing users
            self.console.print("[yellow]No existing users found.[/yellow]\n")
            return Prompt.ask("Enter your username", default="default")
    
    def display_help(self):
        """Display help information."""
        help_text = """
## Available Commands

- **Type any message** - Chat with the AI
- **/memory** - View your current memory
- **/forget** - Clear your memory
- **/users** - List all users
- **/switch** - Switch to a different user
- **/export** - Export your memory
- **/help** - Show this help
- **/exit** or **/quit** - Exit the chatbot

## Tips

- The AI automatically remembers important information
- Your memory persists across sessions
- Each user has their own separate memory
        """
        self.console.print(Panel(
            Markdown(help_text),
            title="📚 Help",
            border_style="blue"
        ))
    
    def display_memory(self):
        """Display current user's memory."""
        if not self.agent:
            return
            
        memory = self.memory_store.read(self.user_id)
        if memory:
            self.console.print(Panel(
                memory,
                title=f"🧠 Memory for {self.user_id}",
                border_style="green"
            ))
        else:
            self.console.print("[yellow]No memories stored yet.[/yellow]")
    
    def export_memory(self):
        """Export memory to a file."""
        if not self.agent:
            return
            
        memory = self.memory_store.read(self.user_id)
        if not memory:
            self.console.print("[yellow]No memory to export.[/yellow]")
            return
            
        filename = f"memory_{self.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write(f"Memory export for {self.user_id}\n")
            f.write(f"Exported on: {datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
            f.write(memory)
        
        self.console.print(f"[green]✓ Memory exported to {filename}[/green]")
    
    def list_users(self):
        """List all users."""
        users = self.memory_store.list_users()
        if users:
            table = Table(title="All Users", box=box.ROUNDED)
            table.add_column("Username", style="cyan")
            table.add_column("Memory Size", style="yellow")
            
            for user in users:
                memory = self.memory_store.read(user)
                size = f"{len(memory)} chars"
                table.add_row(user, size)
            
            self.console.print(table)
        else:
            self.console.print("[yellow]No users found.[/yellow]")
    
    def chat_loop(self):
        """Main chat interaction loop."""
        self.console.print(f"\n[bold green]Chatting as: {self.user_id}[/bold green]")
        self.console.print("Type /help for commands, /exit to quit\n")
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("[bold blue]You[/bold blue]")
                
                # Handle commands
                if user_input.startswith("/"):
                    command = user_input.lower().strip()
                    
                    if command in ["/exit", "/quit"]:
                        break
                    elif command == "/help":
                        self.display_help()
                        continue
                    elif command == "/memory":
                        self.display_memory()
                        continue
                    elif command == "/forget":
                        if Prompt.ask("Are you sure? (y/n)", default="n") == "y":
                            self.memory_store.write(self.user_id, "")
                            self.console.print("[green]✓ Memory cleared[/green]")
                        continue
                    elif command == "/users":
                        self.list_users()
                        continue
                    elif command == "/switch":
                        return True  # Signal to switch users
                    elif command == "/export":
                        self.export_memory()
                        continue
                    else:
                        self.console.print(f"[red]Unknown command: {command}[/red]")
                        continue
                
                # Process chat message
                with self.console.status("[cyan]Thinking...[/cyan]", spinner="dots"):
                    response = self.agent.chat_sync(user_input)
                
                # Display response
                self.console.print()
                self.console.print(
                    Panel(
                        Markdown(response),
                        title="🤖 Assistant",
                        border_style="green",
                        padding=(1, 2)
                    )
                )
                self.console.print()
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use /exit to quit properly[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
    
    def run(self):
        """Run the CLI application."""
        try:
            # Check for API key
            if not os.getenv("ANTHROPIC_API_KEY"):
                self.console.print(
                    "[red]Error: ANTHROPIC_API_KEY environment variable not set![/red]\n"
                )
                self.console.print("Please set it with:")
                self.console.print("[cyan]export ANTHROPIC_API_KEY='your-key-here'[/cyan]")
                return
            
            self.display_banner()
            
            while True:
                # User selection
                self.user_id = self.select_or_create_user()
                
                # Create agent
                self.console.print(f"\n[green]✓ Loading agent for {self.user_id}...[/green]")
                self.agent = MemoryAgent(self.user_id)
                
                # Show current memory status
                memory = self.memory_store.read(self.user_id)
                if memory:
                    self.console.print(f"[dim]Found existing memory ({len(memory)} chars)[/dim]")
                else:
                    self.console.print("[dim]Starting with fresh memory[/dim]")
                
                # Chat loop
                if not self.chat_loop():
                    break  # User wants to exit
                    
                # If we get here, user wants to switch
                self.console.print("\n[yellow]Switching users...[/yellow]\n")
            
            # Goodbye
            self.console.print("\n[bold cyan]Thanks for chatting! Your memories are saved. 👋[/bold cyan]\n")
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Interrupted. Goodbye! 👋[/yellow]\n")
        except Exception as e:
            self.console.print(f"\n[red]Fatal error: {e}[/red]\n")
            raise


def main():
    """Entry point."""
    cli = MemoryChatCLI()
    cli.run()


if __name__ == "__main__":
    main()
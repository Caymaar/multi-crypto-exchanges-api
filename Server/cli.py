import uvicorn
import typer
import subprocess
import os
import sys

app = typer.Typer()

@app.command()
def run(command: str):
    """
    Lancer une commande personnalisée.
    
    Utilisez 'server' pour lancer le serveur via uvicorn,
    ou 'streamlit' pour lancer l'application Streamlit.
    """
    if command == "server":
        typer.echo("Lancement du serveur...")
        sys.path.insert(0, os.path.dirname(__file__))
        uvicorn.run("Server.Server:app", host="0.0.0.0", port=8000)

    # if command == "server":
    #     typer.echo("Synchronisation du code avec uv (server)...")
    #     sys.path.insert(0, os.path.dirname(__file__))
    #     #sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "Server"))
    #     subprocess.run(["uv", "sync"])
    #     typer.echo("Lancement du serveur avec uv run...")
    #     subprocess.run(["uv", "run", "Server/Server.py"])#"uvicorn", "Server:app", "--host", "0.0.0.0", "--port", "8000"])
    elif command == "streamlit":
        typer.echo("Lancement de l'application Streamlit...")
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        # Lance le script Streamlit, ici situé dans le dossier Client
        subprocess.run(["streamlit", "run", "./Client/StreamlitClient.py"])
    elif command == "terminal":
        typer.echo("Lancement du terminal...")
        sys.path.insert(0, os.path.dirname(__file__))
        #sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "Client"))
        try:
            print("Try 1")
            subprocess.run(["uv", "sync"])
            subprocess.run(["uv", "run", "Client/WebsocketClient.py"])
        except:
            try:
                print("Try 2")
                subprocess.run(["uv", "sync"])
                subprocess.run(["uv", "run", "./Client/WebsocketClient.py"])
            except:
                print("Try 3")
                subprocess.run(["uv", "run", "WebsocketClient.py"])

   
        try:
            subprocess.run(["python3", "./Client/WebsocketClient.py"])
        except:
            subprocess.run(["python", "./Client/WebsocketClient.py"])

    else:
        typer.echo(f"Commande inconnue : {command}")

if __name__ == "__main__":
    app()
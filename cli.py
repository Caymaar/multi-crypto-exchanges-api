import uvicorn
import typer
import subprocess
import os, sys

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
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Server"))
        uvicorn.run("Server:app", host="0.0.0.0", port=8000)
    elif command == "streamlit":
        typer.echo("Lancement de l'application Streamlit...")
        # Lance le script Streamlit, ici situé dans le dossier Client
        subprocess.run(["streamlit", "run", "Client/StreamlitClient.py"])
    else:
        typer.echo(f"Commande inconnue : {command}")

if __name__ == "__main__":
    app()
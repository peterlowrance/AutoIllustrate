if (!(Test-Path env)) {
    python3 -m venv env
    & env\Scripts\Activate.ps1
    pip install -r requirements.txt
}



python auto_illustrator.py $args
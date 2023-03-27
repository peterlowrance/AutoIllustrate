Run ./start.sh to run the program (sets up python venv and runs)

Examples:
Using https://github.com/AUTOMATIC1111/stable-diffusion-webui
./start.sh --api-key <OPENAI_API_KEY> --sd-host <YOUR_AUTOMATIC1111_URL>

Using stable horde (https://stablehorde.net)
./start.sh --api-key <OPENAI_API_KEY> --use-horde true

Or using horde account (https://stablehorde.net/register)
./start.sh --api-key <OPENAI_API_KEY> --use-horde true --horde-api-key <HORDE_API_KEY>


Can use environment variable OPENAI_API_KEY for openai key:
export OPENAI_API_KEY=<OPENAI_API_KEY>
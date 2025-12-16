## waitress
- An unorthodox web server
- That does stupid but useful things

1. Use `python main.py --file <filename>` to serve the file and waitress does it immediatly in every network you are connected.
2. Use other arguments to extend functionality
3. `--stream` to stream the file rather than send it at once
4. `--download` to make your browser download the file 
5. jpg, png, wav, html, json -- all are supported

> Please Note! Streaming has strict rules with different browsers, I am working on it so streaming might be just experimental.
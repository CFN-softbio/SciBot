<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CFN Science Chatbot</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>



    <div id="chat-container">

        <div class="header">
            <h1 class="chatbot-title">CFN Science Chatbot</h1>
            <div class="bottom-section">
                <img class="logo" src="logo.png" alt="Logo">
                <div class="description">
                    This is a crude demo of a domain-specific Chatbot. It uses OpenAI's ChatGPT (specifically the GPT-3.5-turbo model) behind the scenes, so it can converse on arbitrary topics in all the ways ChatGPT can. However, it also has access to some domain-specific documents, allowing it to answer questions and discuss topics related to those documents.<br/><br/>
                    Currently, the chatbot has access to Kevin Yager's publications.<br/><br/>
                    For now, the bot only responds to one comment at a time (it can't see the whole history of comments in the current chat window; it only "sees" the last thing you wrote). This means it can't do back-and-forth discussion where you refine a concept.
                </div>
            </div>
        </div>    
    
    
        <div id="chat-area"></div>
        <input type="text" id="message-input" placeholder="Type your message here...">
        <button id="send-button">Send</button>
    </div>
    <script src="script.js"></script>
    
</body>
</html>

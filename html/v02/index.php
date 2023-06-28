<?php
if (!isset($_GET['c'])) {
// On page load, we generate a random conversation ID/token.

function token_urlsafe($length) {
    $randomBytes = random_bytes($length); // Generate random bytes
    $base64 = base64_encode($randomBytes); // Convert to base64
    $urlSafe = strtr($base64, '+/', '-_'); // Replace characters to make it URL safe
    return rtrim($urlSafe, '='); // Remove trailing '='
}

$token = token_urlsafe(16);

// We force this page to reload, but with the token in the URL.
header("Location: index.php?c=".$token);
exit();


}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type">
<title>CFN Science ChatBot</title>
<meta name="description" content="CFN Science ChatBot"/>

<link rel='stylesheet' type='text/css' media='all' href='style.css' />





    <div class="grid_24">
        <h1>CFN Science ChatBot</h1>
    </div>




    <div class="grid_15 suffix_1">
    
        <h3 class="thin baseColor">Demo</h3>
        
        <p class="font-plus-2">This is a demo of a domain-specific ChatBot for science. The chatbot uses a large language model (LLM) for generative text, combined with a database of domain-specific text drawn from CFN publications.</p>

        
        
        
        <div id="chat-container">
            <div id="chat-area"></div>
            <input type="text" id="message-input" placeholder="Type your message here...">
            <button id="send-button">Send</button>
        </div>
        <script src="script.js"></script>

        

        <p class="font-plus-2">&nbsp;</p>

        <p class="font-plus-2">This chatbot architecture is described in this preprint: <a href="https://arxiv.org/abs/2306.10067">Yager, K.G. "Domain-specific ChatBots for Science using Embeddings" arXiv:2306.10067.</a> Source code is available on <a href="https://github.com/CFN-softbio/SciBot">github</a>.</p>

        

    </div>
    <script>window.onload = function() { retrieveConversationHistory(); }</script>













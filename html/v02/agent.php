<?php

function doiToLink($text) {
    $doi_pattern = '/\b(10[.][0-9]{4,}(?:[.][0-9]+)*\/[^ \t\r\n]+)\b/';
    $replacement = '<a href="https://doi.org/$1">$1</a>';
    $text = preg_replace($doi_pattern, $replacement, $text);
    return $text;
}


if (isset($_POST['conversation']) and isset($_POST['message'])) {

    $conversation = $_POST['conversation'];
    $message = $_POST['message'];

    // Connect to SciBot database
    $servername = "localhost";
    $dbname = "SciBot_DocumentStore";
    $username = "scibot";
    $password = "********";

    $conn = new mysqli($servername, $username, $password, $dbname);
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    
    // Add this message into the database
    $stmt = $conn->prepare("INSERT INTO messages (thread_id, date_time, who, message_content) VALUES (?, NOW(), 'user', ?)");
    $stmt->bind_param('ss', $conversation, $message);
    $stmt->execute();
    $stmt->close();
    
    
    // Trigger SciBot
    $command = escapeshellcmd('python3 response.py '.$conversation);
    $script_print = shell_exec($command);
    //echo $script_print;


    // Get reply
    $stmt = $conn->prepare("SELECT * FROM messages WHERE thread_id=? ORDER BY date_time DESC LIMIT 1");
    $stmt->bind_param('s', $conversation);
    $stmt->execute();

    $result = $stmt->get_result(); // Store the result

    if($result->num_rows != 1){ 
        echo "[[db error: expected 1 result, got ".$result->num_rows." results.]]";
    } else {
        $row = $result->fetch_assoc();
        if( $row['who']!='assistant' ) {
            echo "[[reply error: last message is from ".$row['who'].".]]";
        } else {
            $response = nl2br($row['message_content']);
        }
    }

    $stmt->close();
    $conn->close();
    
    // Check for DOIs
    $response = doiToLink($response);
    
    echo $response;
    
    

} else {
    http_response_code(400);
}
?>

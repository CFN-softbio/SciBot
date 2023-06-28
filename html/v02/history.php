<?php
header('Content-Type: application/json');


// Connect to SciBot database
$servername = "localhost";
$dbname = "SciBot_DocumentStore";
$username = "scibot";
$password = "********";

$conn = new mysqli($servername, $username, $password, $dbname);
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}



function doiToLink($text) {
    $doi_pattern = '/\b(10[.][0-9]{4,}(?:[.][0-9]+)*\/[^ \t\r\n]+)\b/';
    $replacement = '<a href="https://doi.org/$1">$1</a>';
    $text = preg_replace($doi_pattern, $replacement, $text);
    return $text;
}



// Get messages
$stmt = $conn->prepare("SELECT who, message_content FROM ( SELECT * FROM messages WHERE thread_id=? ORDER BY date_time DESC LIMIT 100 ) sub ORDER BY date_time ASC;");
$stmt->bind_param("s", $_GET['conversation']);
$stmt->execute();
$stmt->bind_result($sender, $message);

// Fetch values and store in array
$history = array();
while ($stmt->fetch()) {
    if($sender=='assistant') {
        $sender = 'CFNBot';
    }
    $message = doiToLink($message);
    $message = nl2br($message);
    $history[] = array('sender' => $sender, 'message' => $message );
}

// close statement
$stmt->close();

// close connection
$conn->close();

// print JSON string
echo json_encode($history);
?>

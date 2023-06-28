<?php
if (isset($_POST['message'])) {
    $message = $_POST['message'];

    file_put_contents("query.txt", $message);

    $command = escapeshellcmd('python3 response.py');
    $script_print = shell_exec($command);
    //echo $script_print;

    $response = file_get_contents("response.txt");
    echo $response;

} else {
    http_response_code(400);
}
?>

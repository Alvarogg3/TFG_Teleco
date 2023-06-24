// main.js

// Redirect to the create strategy page with null id
document.getElementById('create-strategy-btn').addEventListener('click', function() {
    window.location.href = '/select_stocks/null';
});

// Redirect to the test strategy page
document.getElementById('test-strategy-btn').addEventListener('click', function() {
    window.location.href = '/check_strategies';
});
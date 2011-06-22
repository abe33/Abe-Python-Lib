$(document).ready(function() {
    $("textarea").each(function(n, obj) {
        CKEDITOR.replace( obj.id );
    });    
});


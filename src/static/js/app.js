$(document).ready(function() {
    setTimeout(function(){
        document.getElementById("alert").style.display = "none";
    }, 3000);
    
    $('#conversationEdit').on('shown.bs.modal', function(event) {
        var button = $(event.relatedTarget); // Botón que abrió el modal
        var id = button.data('id'); // Obtener el valor del atributo data-id
        var question = button.data('question'); // Obtener el valor del atributo data-question
        var answer = button.data('answer'); // Obtener el valor del atributo data-answer
        // Insertar los valores en los campos del formulario dentro del modal
        $(this).find('#editId').val(id); // Asignar el valor del ID al campo oculto
        $(this).find('textarea[name="question"]').val(question);
        $(this).find('textarea[name="answer"]').val(answer);
    });
});
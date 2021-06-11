
  $('.update-movie').click(function() {
    movie_id = $(this).attr('id');
    target = $(this).find('i');
    if($(this).hasClass('update-watched')){
      change = 'watched';
    }
    if($(this).hasClass('update-saved')){
      change = 'saved';
    }
    $.ajax({
      type: "POST",
      url: "/movie/"+movie_id+"/",
      data: {
        'change': change,
      },
      success: function(data, textStatus, jqXhr) {
        target.toggleClass('text-dark');
        target.toggleClass('text-primary');
        console.log(data);
      },
      error: function(jqXhr, textStatus, errorThrown) {
        console.log(jqXhr);
        console.log(textStatus);
        console.log(errorThrown);
      }
    });
    return false;
  });


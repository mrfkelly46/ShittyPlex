function hasAudio(video) {
    return video.mozHasAudio ||
    Boolean(video.webkitAudioDecodedByteCount) ||
    Boolean(video.audioTracks && video.audioTracks.length);
}

function hasVideo(video) {
    // No need for this.
    //   If video works, then it comes down to adio only.
    //   If video doesnt work, then audio doesnt autoplay and hasAudio() returns false.
    return true;
}

function message(msg, type) {
    msgString = `
      <div class="alert alert-${type} alert-dismissible mt-3" role="alert"> 
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
        ${msg}
      </div>
    `;
    document.getElementById("messages").innerHTML += msgString;
}

async function streamable(video) {
  await new Promise(r => setTimeout(r, 1500));
  if(!hasAudio(video)) {
    console.log("Video is BAD!");
    message("Unsupported codec, browser playback is unavailable.<br>To play in VLC, right click \"Copy video address...\", Open VLC and press <kbd>CTRL + N</kbd> and paste the video address.", "danger");
  } else {
    console.log("Video is OK!");
  }
}


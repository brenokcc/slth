import { useState, useEffect } from "react";
import Icon from "./Icon";
import { showMessage } from "./Message";

function WebConf(props) {
  var peer = null;
  var localStream = null;
  var remoteStream = null;
  var connected = false;
  var interval = null;
  var getUserMedia =
    navigator.getUserMedia ||
    navigator.webkitGetUserMedia ||
    navigator.mozGetUserMedia;
  var options = {
    constraints: {
      mandatory: {
        OfferToReceiveAudio: true,
        OfferToReceiveVideo: true,
      },
      offerToReceiveAudio: 1,
      offerToReceiveVideo: 1,
    },
    sdpTransform: (test) => {
      return test.replace(
        "a=fmtp:111 minptime=10;useinbandfec=1",
        "a=fmtp:111 ptime=5;useinbandfec=1;stereo=1;maxplaybackrate=48000;maxaveragebitrat=128000;sprop-stereo=1"
      );
    },
  };

  useEffect(() => {
    peer = new Peer("123456" + props.data.caller.replaceAll(".", ""));
    peer.on("open", function (id) {
      document.getElementById("callerid").innerHTML = props.data.caller;
      start()
    });
    peer.on("call", function (call) {
      getUserMedia(
        {
          video: { width: { exact: 320 }, height: { exact: 240 } },
          audio: true,
        },
        function (stream) {
          localStream = stream;
          var video = document.getElementById("video2");
          video.addEventListener(
            "loadedmetadata",
            function (e) {
              video.style.width = this.videoWidth / 4 + "px";
              video.style.height = this.videoHeight / 4 + "px";
              video.style.marginLeft = -this.videoWidth / 4 + "px";
              video.style.visibility = "visible";
            },
            false
          );
          video.srcObject = localStream;
          call.answer(stream);
          call.on("stream", function (stream) {
            remoteStream = stream;
            document.getElementById("video1").srcObject = remoteStream;
            connected = true;
          });
          call.on("close", function () {
            //stop();
            console.log('Closed!');
            connected = false;
          });
          peer.on("error", function (err) {
            //stop();
            console.log('Error!');
            connected = false;
          });
        },
        function (err) {
          console.log("Failed to get local stream", err);
        }
      );
    });
    peer.on("error", function (err) {
      if (err.type == "browser-incompatible") {
        alert("Navegador incompatível.");
      } else if (err.type == "invalid-id") {
        alert("Usuário inexistente.");
      } else if (err.type == "network") {
        alert("Problema na conexão do usuário.");
      } else if (err.type == "peer-unavailable") {
        console.log('Usuário indisponível!');
        connected = false;
      }
    });
    interval = setInterval(function(){
      if(connected){
        showMessage("Em conexão com "+props.data.receiver+".");
      } else {
        showMessage("Tentando estabeler conexão com "+props.data.receiver+"...");
        start();
      }
    }, 15000);
    return function(){
      clearInterval(interval);
      stop();
      showMessage("Desconectado!");
    }
  }, []);

  function pause() {
    pause_track(localStream, "audio");
    pause_track(localStream, "video");
    pause_track(remoteStream, "audio");
    pause_track(remoteStream, "video");
  }

  function resume() {
    resume_track(localStream, "audio");
    resume_track(localStream, "video");
    resume_track(remoteStream, "audio");
    resume_track(remoteStream, "video");
  }

  function stop() {
    stop_track(localStream, "audio");
    stop_track(localStream, "video");
    stop_track(remoteStream, "audio");
    stop_track(remoteStream, "video");
    localStream = null;
    remoteStream = null;
    const video1 = document.getElementById("video1");
    const video2 = document.getElementById("video2");
    if (video1) video1.srcObject = null;
    if (video2) video2.srcObject = null;
    console.log("Stopped!");
  }

  function stop_track(stream, kind) {
    if (stream != null)
      stream.getTracks().forEach((track) => {
        if (track.kind === kind) {
          track.stop();
        }
      });
  }

  function pause_track(stream, kind) {
    if (stream != null)
      stream.getTracks().forEach((track) => {
        if (track.readyState == "live" && track.kind === kind) {
          track.enabled = false;
        }
      });
  }

  function resume_track(stream, kind) {
    if (stream != null)
      stream.getTracks().forEach((track) => {
        if (track.readyState == "live" && track.kind === kind) {
          track.enabled = true;
        }
      });
  }

  function plus() {
    var video = document.getElementById("video1");
    video.style.width = video.getClientRects()[0].width + 100 + "px";
  }

  function minus() {
    var video = document.getElementById("video1");
    video.style.width = video.getClientRects()[0].width - 100 + "px";
  }

  function call() {
    var call = peer.call(
      "123456" + props.data.receiver.replaceAll(".", ""),
      localStream,
      options
    );
    call.on("stream", function (stream) {
      remoteStream = stream;
      document.getElementById("video1").srcObject = remoteStream;
      connected = true;
    });
    call.on("close", function () {
      //stop();
      console.log('Closed!');
      connected = false;
    });
    peer.on("error", function (err) {
      //stop();
      console.log('Error!');
      connected = false;
    });
  }

  function start() {
    if (localStream != null && !connected) return call();
    //if (localStream != null && remoteStream != null) return resume();
    getUserMedia(
      {
        video: { width: { exact: 320 }, height: { exact: 240 } },
        audio: {
          autoGainControl: false,
          channelCount: 2,
          echoCancellation: false,
          latency: 0,
          noiseSuppression: false,
          sampleRate: 48000,
          sampleSize: 16,
          volume: 1.0,
        },
      },
      function (stream) {
        localStream = stream;
        var video = document.getElementById("video2");
        video.addEventListener(
          "loadedmetadata",
          function (e) {
            video.style.width = this.videoWidth / 4 + "px";
            video.style.height = this.videoHeight / 4 + "px";
            video.style.marginLeft = -this.videoWidth / 4 + "px";
            video.style.visibility = "visible";
          },
          false
        );
        video.srcObject = localStream;
        call();
      },
      function (err) {
        alert("Failed to get local stream.");
      }
    );
  }

  function render() {
    var player = { width: "fit-content", margin: "auto" };
    var text = { position: "absolute", color: "white", padding: "5px" };
    var icon = { color: "white", backgroundColor: "black", padding: 2 };
    var controls = { position: "absolute", marginTop: "-30px" };
    var video1 = { backgroundColor: "black" };
    var video2 = { visibility: "hidden", width: "0px" };
    return (
      <div style={player}>
        <div id="callerid" style={text}></div>
        <video id="video1" style={video1} playsInline autoPlay></video>
        <video id="video2" style={video2} playsInline autoPlay></video>
        <div style={controls}>
          <Icon style={icon} onClick={pause} icon="pause" />
          <Icon style={icon} onClick={stop} icon="stop" />
          <Icon style={icon} onClick={plus} icon="search-plus" />
          <Icon style={icon} onClick={minus} icon="search-minus" />
        </div>
      </div>
    );
  }

  return render();
}

export { WebConf };
export default WebConf;

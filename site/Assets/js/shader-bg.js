/* Endless Summer — audio-reactive WebGL gradient background (site-wide).
   Vanilla-JS port of the Figma/React component. Same shader + same audio
   beat-reactivity; runs on a fixed full-viewport <canvas> behind all content.
   - Click passes through (pointer-events:none); mouse parallax via window listener.
   - Respects prefers-reduced-motion (renders one static frame, no audio autostart).
   - Audio is opt-in: starts paused (browsers block autoplay-with-sound).
   Drop your licensed track at Assets/audio/track.mp3 (see AUDIO_SRC). */
(function () {
  "use strict";

  var AUDIO_SRC = "Assets/audio/track.mp3"; // replace with your track (root-relative)
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var vertexShaderSource =
    "attribute vec2 a_position;void main(){gl_Position=vec4(a_position,0,1);}";

  var fragmentShaderSource = [
    "precision mediump float;",
    "uniform vec2 iResolution;",
    "uniform float iTime;",
    "uniform float uSpeed;",
    "uniform float uLineCount;",
    "uniform float uAmplitude;",
    "uniform float uYOffset;",
    "uniform vec2 uMouse;",
    "uniform float uBeat;",
    "const float MAX_LINES = 20.0;",
    "float wave(vec2 uv,float speed,float yPos,float thickness,float softness,float mouseInfluence){",
    "  float falloff = smoothstep(1.,0.5,abs(uv.x));",
    "  float y = falloff*sin(iTime*speed+uv.x*10.0+mouseInfluence)*yPos-uYOffset;",
    "  return 1.0-smoothstep(thickness,thickness+softness,abs(uv.y-y));",
    "}",
    "void main(){",
    "  vec2 uv = gl_FragCoord.xy/iResolution.y;",
    "  vec4 col = vec4(0.0,0.0,0.0,1.0);",
    "  vec3 gradCol1 = vec3(0.2,0.1,0.0);",
    "  vec3 gradCol2 = vec3(0.2,0.0,0.2);",
    "  col.xyz = mix(gradCol1,gradCol2,uv.x+uv.y);",
    "  uv -= 0.5;",
    "  const vec3 col1 = vec3(0.2,0.5,0.9);", // electric blue
    "  const vec3 col2 = vec3(0.9,0.3,0.9);", // hot pink / magenta
    "  float aaDy = iResolution.y*0.000005;",
    "  float mousePhase = uMouse.x*10.0;",
    "  float mouseAmp = 1.0+uMouse.y*0.5;",
    "  for(float i=0.;i<MAX_LINES;i+=1.){",
    "    if(i<=uLineCount){",
    "      float t = i/(uLineCount-1.0);",
    "      vec3 lineCol = mix(col1,col2,t);",
    "      float bokeh = pow(t,3.0);",
    "      float thickness = 0.003;",
    "      float softness = aaDy+bokeh*0.2;",
    "      float amp = (uAmplitude-0.05*t)*mouseAmp*(1.0+uBeat);",
    "      float amt = max(0.0,pow(1.0-bokeh,2.0)*0.9);",
    "      col.xyz += wave(uv,uSpeed*(1.0+t),amp,thickness,softness,mousePhase)*lineCol*amt;",
    "    }",
    "  }",
    "  gl_FragColor = col;",
    "}"
  ].join("\n");

  // tunables (mirror the component defaults)
  var SPEED = 1.0, LINE_COUNT = 10, AMPLITUDE = 0.15, Y_OFFSET = 0.15;

  var gl, program, uniforms = {}, canvas;
  var startTime = Date.now();
  var mouse = { x: 0.5, y: 0.5 };
  var audio = { el: null, ctx: null, analyser: null, data: null, beat: 0 };
  var rafId = null;

  function createShader(type, source) {
    var s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.error(gl.getShaderInfoLog(s));
      return null;
    }
    return s;
  }

  function initGL() {
    canvas = document.createElement("canvas");
    canvas.id = "bg-shader";
    canvas.setAttribute("aria-hidden", "true");
    document.body.appendChild(canvas);

    gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    if (!gl) { canvas.parentNode.removeChild(canvas); return false; }

    program = gl.createProgram();
    var v = createShader(gl.VERTEX_SHADER, vertexShaderSource);
    var f = createShader(gl.FRAGMENT_SHADER, fragmentShaderSource);
    if (!v || !f) { canvas.parentNode.removeChild(canvas); return false; }
    gl.attachShader(program, v);
    gl.attachShader(program, f);
    gl.linkProgram(program);
    gl.useProgram(program);

    var buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(
      [-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(program, "a_position");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    ["iResolution", "iTime", "uSpeed", "uLineCount", "uAmplitude", "uYOffset", "uMouse", "uBeat"]
      .forEach(function (n) { uniforms[n] = gl.getUniformLocation(program, n); });
    return true;
  }

  function resize() {
    if (!canvas || !gl) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2); // cap DPR for perf
    var w = window.innerWidth, h = window.innerHeight;
    if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      gl.viewport(0, 0, canvas.width, canvas.height);
    }
  }

  function updateAudio() {
    if (!audio.analyser || !audio.data) return;
    audio.analyser.getByteFrequencyData(audio.data);
    var sum = 0;
    for (var i = 0; i < audio.data.length; i++) sum += audio.data[i];
    audio.beat = (sum / audio.data.length) / 255;
  }

  function draw() {
    if (!gl || !uniforms.iResolution) return;
    var t = (Date.now() - startTime) / 1000;
    if (audio.analyser) updateAudio();
    gl.uniform2f(uniforms.iResolution, canvas.width, canvas.height);
    gl.uniform1f(uniforms.iTime, t);
    gl.uniform1f(uniforms.uSpeed, SPEED);
    gl.uniform1f(uniforms.uLineCount, LINE_COUNT);
    gl.uniform1f(uniforms.uAmplitude, AMPLITUDE);
    gl.uniform1f(uniforms.uYOffset, Y_OFFSET);
    gl.uniform2f(uniforms.uMouse, mouse.x, mouse.y);
    gl.uniform1f(uniforms.uBeat, audio.beat);
    gl.drawArrays(gl.TRIANGLES, 0, 6);
  }

  function loop() { draw(); rafId = requestAnimationFrame(loop); }

  // -------- audio player UI --------
  function buildPlayer() {
    var el = document.createElement("audio");
    el.src = AUDIO_SRC;
    el.loop = true;
    el.preload = "none";
    audio.el = el;

    var wrap = document.createElement("div");
    wrap.className = "bg-audio";
    wrap.innerHTML =
      '<button type="button" class="bg-audio__btn" aria-label="Play music">▶</button>' +
      '<span class="bg-audio__label">Vibe</span>' +
      '<input class="bg-audio__vol" type="range" min="0" max="1" step="0.01" value="0.5" aria-label="Volume">';
    var btn = wrap.querySelector(".bg-audio__btn");
    var vol = wrap.querySelector(".bg-audio__vol");
    el.volume = 0.5;

    function ensureCtx() {
      if (audio.ctx) return;
      try {
        var AC = window.AudioContext || window.webkitAudioContext;
        audio.ctx = new AC();
        audio.analyser = audio.ctx.createAnalyser();
        audio.analyser.fftSize = 256;
        var src = audio.ctx.createMediaElementSource(el);
        src.connect(audio.analyser);
        audio.analyser.connect(audio.ctx.destination);
        audio.data = new Uint8Array(audio.analyser.frequencyBinCount);
      } catch (e) { /* analyser optional; playback still works */ }
    }

    btn.addEventListener("click", function () {
      ensureCtx();
      if (audio.ctx && audio.ctx.state === "suspended") audio.ctx.resume();
      if (el.paused) {
        el.play().then(function () {
          btn.textContent = "❚❚"; btn.setAttribute("aria-label", "Pause music");
        }).catch(function () { /* no file / blocked */ });
      } else {
        el.pause();
        btn.textContent = "▶"; btn.setAttribute("aria-label", "Play music");
      }
    });
    vol.addEventListener("input", function () { el.volume = parseFloat(vol.value); });

    document.body.appendChild(wrap);
  }

  function init() {
    if (!initGL()) return; // WebGL unavailable -> fallback solid bg (html bg)
    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", function (e) {
      mouse.x = e.clientX / window.innerWidth;
      mouse.y = 1 - e.clientY / window.innerHeight;
    }, { passive: true });

    buildPlayer();

    if (REDUCED) { draw(); return; } // one static frame, no animation/audio loop
    loop();
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { if (rafId) { cancelAnimationFrame(rafId); rafId = null; } }
      else if (!rafId) { loop(); }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();

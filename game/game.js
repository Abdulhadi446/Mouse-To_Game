const scene = new THREE.Scene();
scene.background = new THREE.Color(0x9ed0ff);
scene.fog = new THREE.Fog(0x9ed0ff, 220, 620);

const camera = new THREE.PerspectiveCamera(
  72,
  window.innerWidth / window.innerHeight,
  0.5,
  900,
);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

const hemi = new THREE.HemisphereLight(0xffffff, 0x3a5721, 0.72);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xffffff, 0.9);
sun.position.set(140, 170, 80);
sun.castShadow = true;
sun.shadow.mapSize.width = 2048;
sun.shadow.mapSize.height = 2048;
sun.shadow.camera.near = 0.5;
sun.shadow.camera.far = 520;
scene.add(sun);

const fillLight = new THREE.DirectionalLight(0xfff1d6, 0.25);
fillLight.position.set(-120, 90, -60);
scene.add(fillLight);

const grass = new THREE.Mesh(
  new THREE.PlaneGeometry(1200, 1200),
  new THREE.MeshLambertMaterial({ color: 0x3a6f2a }),
);
grass.rotation.x = -Math.PI / 2;
grass.position.y = -0.2;
grass.receiveShadow = true;
scene.add(grass);

const trackA = 160;
const trackB = 105;
const trackHalfWidth = 22;

const road = new THREE.Mesh(
  new THREE.RingGeometry(trackB - trackHalfWidth, trackA + trackHalfWidth, 128),
  new THREE.MeshLambertMaterial({ color: 0x2f2f31, side: THREE.FrontSide }),
);
road.rotation.x = -Math.PI / 2;
road.position.y = 0.03;
road.receiveShadow = true;
scene.add(road);

const innerDirt = new THREE.Mesh(
  new THREE.CircleGeometry(trackB - trackHalfWidth - 3, 90),
  new THREE.MeshLambertMaterial({ color: 0x6f5a3f }),
);
innerDirt.rotation.x = -Math.PI / 2;
innerDirt.position.y = 0.01;
scene.add(innerDirt);

const townGround = new THREE.Mesh(
  new THREE.CircleGeometry(68, 64),
  new THREE.MeshLambertMaterial({ color: 0x89806d }),
);
townGround.rotation.x = -Math.PI / 2;
townGround.position.y = 0.045;
townGround.receiveShadow = true;
scene.add(townGround);

const townRoad = new THREE.Mesh(
  new THREE.PlaneGeometry(120, 16),
  new THREE.MeshLambertMaterial({ color: 0x3a3a3a }),
);
townRoad.rotation.x = -Math.PI / 2;
townRoad.position.y = 0.06;
scene.add(townRoad);

const townRoadCross = townRoad.clone();
townRoadCross.rotation.z = Math.PI / 2;
scene.add(townRoadCross);

const townSidewalkMat = new THREE.MeshLambertMaterial({ color: 0xbcb4a6 });
const townSidewalk = new THREE.Mesh(
  new THREE.PlaneGeometry(120, 5),
  townSidewalkMat,
);
townSidewalk.rotation.x = -Math.PI / 2;
townSidewalk.position.set(0, 0.075, 10.5);
scene.add(townSidewalk);

const townSidewalk2 = townSidewalk.clone();
townSidewalk2.position.z = -10.5;
scene.add(townSidewalk2);

const townSidewalk3 = new THREE.Mesh(
  new THREE.PlaneGeometry(5, 120),
  townSidewalkMat,
);
townSidewalk3.rotation.x = -Math.PI / 2;
townSidewalk3.position.set(10.5, 0.075, 0);
scene.add(townSidewalk3);

const townSidewalk4 = townSidewalk3.clone();
townSidewalk4.position.x = -10.5;
scene.add(townSidewalk4);

const centerLineMat = new THREE.MeshBasicMaterial({ color: 0xf5f08b });
for (let i = 0; i < 90; i += 1) {
  const t = (i / 90) * Math.PI * 2;
  const x = Math.cos(t) * ((trackA + trackB) / 2);
  const z = Math.sin(t) * ((trackA + trackB) / 2);
  const dash = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 7), centerLineMat);
  dash.position.set(x, 0.09, z);
  dash.rotation.x = -Math.PI / 2;
  dash.rotation.z = t;
  scene.add(dash);
}

function makeTree(x, z) {
  const trunk = new THREE.Mesh(
    new THREE.CylinderGeometry(1.1, 1.3, 8, 10),
    new THREE.MeshPhongMaterial({ color: 0x6b4a2a }),
  );
  trunk.position.set(x, 4, z);
  trunk.castShadow = true;

  const leaves = new THREE.Mesh(
    new THREE.SphereGeometry(4.8, 10, 10),
    new THREE.MeshPhongMaterial({ color: 0x2f7f2f }),
  );
  leaves.position.set(x, 10, z);
  leaves.castShadow = true;

  const g = new THREE.Group();
  g.add(trunk);
  g.add(leaves);
  scene.add(g);
}

for (let i = 0; i < 360; i += 12) {
  const r = (i * Math.PI) / 180;
  makeTree(Math.cos(r) * 250, Math.sin(r) * 190);
}

const buildingColliders = [];

function addBuildingCollider(x, z, w, d, margin = 0.9) {
  buildingColliders.push({
    minX: x - w / 2 - margin,
    maxX: x + w / 2 + margin,
    minZ: z - d / 2 - margin,
    maxZ: z + d / 2 + margin,
  });
}

function createLabelTexture(text, bgColor = "#203040") {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 96;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#f5f4d7";
  ctx.lineWidth = 6;
  ctx.strokeRect(6, 6, canvas.width - 12, canvas.height - 12);
  ctx.fillStyle = "#f5f4d7";
  ctx.font = "bold 34px Arial";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

function createBuilding({ x, z, w, h, d, color, roofColor }) {
  const group = new THREE.Group();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(w, h, d),
    new THREE.MeshPhongMaterial({ color }),
  );
  base.position.y = h / 2;
  base.castShadow = true;
  base.receiveShadow = true;
  group.add(base);

  const roof = new THREE.Mesh(
    new THREE.ConeGeometry(Math.max(w, d) * 0.7, 1.9, 4),
    new THREE.MeshPhongMaterial({ color: roofColor }),
  );
  roof.position.y = h + 1.2;
  roof.rotation.y = Math.PI / 4;
  roof.castShadow = true;
  group.add(roof);

  const door = new THREE.Mesh(
    new THREE.BoxGeometry(1.2, 2.2, 0.2),
    new THREE.MeshPhongMaterial({ color: 0x4a3522 }),
  );
  door.position.set(0, 1.1, d / 2 + 0.11);
  group.add(door);

  group.position.set(x, 0, z);
  scene.add(group);
  addBuildingCollider(x, z, w, d);
}

function createShop({ x, z, w, h, d, color, signColor, name, rotY = 0 }) {
  const group = new THREE.Group();

  const body = new THREE.Mesh(
    new THREE.BoxGeometry(w, h, d),
    new THREE.MeshPhongMaterial({ color }),
  );
  body.position.y = h / 2;
  body.castShadow = true;
  body.receiveShadow = true;
  group.add(body);

  const awning = new THREE.Mesh(
    new THREE.BoxGeometry(w + 0.5, 0.35, 1.1),
    new THREE.MeshPhongMaterial({ color: 0xf2e0b6 }),
  );
  awning.position.set(0, h * 0.6, d / 2 + 0.3);
  awning.castShadow = true;
  group.add(awning);

  const sign = new THREE.Mesh(
    new THREE.BoxGeometry(w * 0.55, 0.7, 0.18),
    new THREE.MeshPhongMaterial({ color: signColor }),
  );
  sign.position.set(0, h + 0.5, d / 2 + 0.15);
  sign.castShadow = true;
  group.add(sign);

  const label = new THREE.Mesh(
    new THREE.PlaneGeometry(w * 0.52, 0.85),
    new THREE.MeshBasicMaterial({
      map: createLabelTexture(name, "#1f2a38"),
      transparent: false,
    }),
  );
  label.position.set(0, h + 0.5, d / 2 + 0.26);
  group.add(label);

  const sideGlass = new THREE.Mesh(
    new THREE.BoxGeometry(w * 0.65, 1.2, 0.15),
    new THREE.MeshPhongMaterial({
      color: 0xaad7ef,
      transparent: true,
      opacity: 0.55,
    }),
  );
  sideGlass.position.set(0, 2.2, d / 2 + 0.12);
  group.add(sideGlass);

  group.position.set(x, 0, z);
  group.rotation.y = rotY;
  scene.add(group);
  addBuildingCollider(x, z, w, d);
}

// Town center in the middle area so player can drive through it.
createBuilding({
  x: -42,
  z: -36,
  w: 15,
  h: 10,
  d: 9,
  color: 0xe8d5bc,
  roofColor: 0xa3472d,
});
createBuilding({
  x: 43,
  z: -34,
  w: 13,
  h: 9,
  d: 9,
  color: 0xc7d8ec,
  roofColor: 0x5b4d3b,
});
createBuilding({
  x: -44,
  z: 36,
  w: 14,
  h: 9,
  d: 11,
  color: 0xd6e5c1,
  roofColor: 0x8a3026,
});

createBuilding({
  x: 42,
  z: 36,
  w: 13,
  h: 8.5,
  d: 10,
  color: 0xf2d6c5,
  roofColor: 0x6a3f2c,
});

createShop({
  x: 0,
  z: -47,
  w: 16,
  h: 7,
  d: 8,
  color: 0xf3ddb0,
  signColor: 0x2f63dd,
  name: "MARKET",
});
createShop({
  x: -47,
  z: 0,
  w: 15,
  h: 6.5,
  d: 7,
  color: 0xc8efdc,
  signColor: 0xe0b326,
  name: "CAFE",
  rotY: Math.PI / 2,
});
createShop({
  x: 47,
  z: 0,
  w: 15,
  h: 6.5,
  d: 7,
  color: 0xf2c4c4,
  signColor: 0x8b3dd8,
  name: "GARAGE",
  rotY: -Math.PI / 2,
});

createShop({
  x: 0,
  z: 47,
  w: 16,
  h: 7,
  d: 8,
  color: 0xd8d1f7,
  signColor: 0x2f8d5a,
  name: "BAKERY",
  rotY: Math.PI,
});

const checkpointAngles = [0, Math.PI / 2, Math.PI, (3 * Math.PI) / 2];
const checkpointState = checkpointAngles.map(() => false);
const checkpoints = [];

checkpointAngles.forEach((angle, idx) => {
  const x = Math.cos(angle) * ((trackA + trackB) * 0.5);
  const z = Math.sin(angle) * ((trackA + trackB) * 0.5);
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(5.5, 0.6, 10, 24),
    new THREE.MeshPhongMaterial({ color: idx === 0 ? 0x5cf49e : 0x5c8ef4 }),
  );
  ring.position.set(x, 4.5, z);
  ring.rotation.x = Math.PI / 2;
  ring.castShadow = true;
  scene.add(ring);
  checkpoints.push({ x, z, ring });
});

const pickups = [];

function createPickup(x, z) {
  const orb = new THREE.Mesh(
    new THREE.SphereGeometry(1.1, 12, 12),
    new THREE.MeshPhongMaterial({ color: 0xffd764, emissive: 0x5a4200 }),
  );
  orb.position.set(x, 1.5, z);
  orb.castShadow = true;
  scene.add(orb);
  pickups.push({ x, z, orb, active: true, respawnMs: 0 });
}

[
  [-28, -10],
  [26, -14],
  [0, 16],
  [-14, 30],
  [18, 32],
  [34, 6],
].forEach(([x, z]) => createPickup(x, z));

function isBlockedByBuilding(x, z) {
  for (let i = 0; i < buildingColliders.length; i += 1) {
    const b = buildingColliders[i];
    if (x >= b.minX && x <= b.maxX && z >= b.minZ && z <= b.maxZ) {
      return true;
    }
  }
  return false;
}

function buildCar(color) {
  const car = new THREE.Group();

  const body = new THREE.Mesh(
    new THREE.BoxGeometry(2.1, 1.1, 4.2),
    new THREE.MeshPhongMaterial({ color, shininess: 45 }),
  );
  body.position.y = 1;
  body.castShadow = true;
  car.add(body);

  const cabin = new THREE.Mesh(
    new THREE.BoxGeometry(1.8, 0.7, 1.8),
    new THREE.MeshPhongMaterial({
      color: 0xa9d8ff,
      transparent: true,
      opacity: 0.7,
    }),
  );
  cabin.position.set(0, 1.7, -0.2);
  cabin.castShadow = true;
  car.add(cabin);

  const wheelGeo = new THREE.CylinderGeometry(0.48, 0.48, 0.42, 14);
  const wheelMat = new THREE.MeshPhongMaterial({ color: 0x111111 });
  const wheelOffsets = [
    [-1, 1.45],
    [1, 1.45],
    [-1, -1.45],
    [1, -1.45],
  ];

  const wheels = [];
  wheelOffsets.forEach(([x, z]) => {
    const wheel = new THREE.Mesh(wheelGeo, wheelMat);
    wheel.rotation.z = Math.PI / 2;
    wheel.position.set(x, 0.55, z);
    wheel.castShadow = true;
    car.add(wheel);
    wheels.push(wheel);
  });

  return { car, wheels };
}

const playerBuilt = buildCar(0xcf3131);
const playerCar = playerBuilt.car;
const playerWheels = playerBuilt.wheels;
scene.add(playerCar);

const aiCars = [];
[0x2f63dd, 0xe0b326, 0x8b3dd8].forEach((color, idx) => {
  const built = buildCar(color);
  scene.add(built.car);
  aiCars.push({
    mesh: built.car,
    wheels: built.wheels,
    wheelSpin: 0,
    angle: (idx * Math.PI * 2) / 3,
    speed: 0.007 + idx * 0.001,
  });
});

const input = {
  throttle: 0,
  leftHeld: false,
  rightHeld: false,
  brakeHeld: false,
  mapperEnabled: true,
  wheelCounter: 0,
  forwardLatched: false,
  backwardLatched: false,
};

const mapperConfig = {
  wheelStep: 0.35,
  wheelPressThreshold: 1.0,
  wheelReleaseThreshold: 0.5,
};

const state = {
  x: trackA,
  z: 0,
  yaw: Math.PI / 2,
  speed: 0,
  vx: 0,
  vz: 0,
  yawVel: 0,
  wheelSpin: 0,
  mass: 1350,
  inertia: 1800,
  maxForwardSpeed: 62,
  maxReverseSpeed: -14,
  engineForceMax: 9800,
  brakeForceMax: 14000,
  rollingResistance: 12,
  airDrag: 0.42,
  wheelBase: 2.7,
  axleTrack: 1.55,
  frontAxleToCG: 1.2,
  rearAxleToCG: 1.5,
  wheelRadius: 0.34,
  suspensionRestLength: 0.34,
  suspensionTravel: 0.16,
  springRate: 34000,
  damperRate: 3600,
  antiRoll: 9000,
  wheelAngularVel: 0,
  maxSteerAngle: 0.58,
  steerSpeedFactor: 0.024,
  cornerStiffFrontRoad: 8.4,
  cornerStiffRearRoad: 9.0,
  cornerStiffFrontOffroad: 3.2,
  cornerStiffRearOffroad: 3.8,
  tractionLimitRoad: 1.08,
  tractionLimitOffroad: 0.62,
  throttleStep: 0.18,
  score: 0,
  surface: "Road",
  lap: 0,
  lapStartMs: performance.now(),
  bestLapMs: null,
  canCountLap: true,
};

const hud = {
  speed: document.getElementById("speed"),
  gear: document.getElementById("gear"),
  rpm: document.getElementById("rpm"),
  surface: document.getElementById("surface"),
  lap: document.getElementById("lap"),
  lapTime: document.getElementById("lapTime"),
  bestTime: document.getElementById("bestTime"),
  score: document.getElementById("score"),
  mapperState: document.getElementById("mapperState"),
  wheelCounter: document.getElementById("wheelCounter"),
  wheelAction: document.getElementById("wheelAction"),
  message: document.getElementById("message"),
};

const minimap = document.getElementById("minimap");
const mapCtx = minimap.getContext("2d");
let lastFrameMs = performance.now();

function formatMs(ms) {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function showMessage(text, duration = 1300) {
  hud.message.textContent = text;
  clearTimeout(showMessage.tid);
  showMessage.tid = setTimeout(() => {
    hud.message.textContent = "";
  }, duration);
}

function resetPlayer() {
  state.x = trackA;
  state.z = 0;
  state.yaw = Math.PI / 2;
  state.speed = 0;
  state.vx = 0;
  state.vz = 0;
  state.yawVel = 0;
  state.wheelAngularVel = 0;
  input.throttle = 0;
  input.wheelCounter = 0;
  input.forwardLatched = false;
  input.backwardLatched = false;
}

function updateWheelLatchState() {
  if (input.wheelCounter >= mapperConfig.wheelPressThreshold) {
    input.forwardLatched = true;
    input.backwardLatched = false;
  } else if (
    input.forwardLatched &&
    input.wheelCounter <= mapperConfig.wheelReleaseThreshold
  ) {
    input.forwardLatched = false;
  }

  if (input.wheelCounter <= -mapperConfig.wheelPressThreshold) {
    input.backwardLatched = true;
    input.forwardLatched = false;
  } else if (
    input.backwardLatched &&
    input.wheelCounter >= -mapperConfig.wheelReleaseThreshold
  ) {
    input.backwardLatched = false;
  }
}

function applyWheelNotch(direction, magnitude = 1) {
  if (!input.mapperEnabled) return;
  const step = mapperConfig.wheelStep * Math.max(0, magnitude);
  input.wheelCounter = THREE.MathUtils.clamp(
    input.wheelCounter + (direction > 0 ? step : -step),
    -1,
    1,
  );
  updateWheelLatchState();
}

function emergencyStop() {
  input.wheelCounter = 0;
  input.forwardLatched = false;
  input.backwardLatched = false;
  input.throttle = 0;
  state.vx = 0;
  state.vz = 0;
  state.speed = 0;
  state.yawVel = 0;
  state.wheelAngularVel = 0;
  showMessage("EMERGENCY STOP", 900);
}

function toggleMapper() {
  input.mapperEnabled = !input.mapperEnabled;
  if (!input.mapperEnabled) {
    emergencyStop();
  }
  showMessage(input.mapperEnabled ? "MAPPER ENABLED" : "MAPPER DISABLED", 900);
}

document.addEventListener(
  "wheel",
  (e) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      applyWheelNotch(1, 1);
    } else {
      applyWheelNotch(-1, 1);
    }
  },
  { passive: false },
);

document.addEventListener("mousedown", (e) => {
  if (e.button === 0) input.leftHeld = true;
  if (e.button === 2) input.rightHeld = true;
  if (e.button === 1) {
    input.brakeHeld = true;
    emergencyStop();
  }
});

document.addEventListener("mouseup", (e) => {
  if (e.button === 0) input.leftHeld = false;
  if (e.button === 2) input.rightHeld = false;
  if (e.button === 1) input.brakeHeld = false;
});

document.addEventListener("contextmenu", (e) => e.preventDefault());

document.addEventListener("keydown", (e) => {
  const key = e.key.toLowerCase();
  if (key === "r") {
    resetPlayer();
    showMessage("RESET");
  }
  if (key === "f8") {
    toggleMapper();
  }
});

const boostPads = [];
function createBoostPad(angle, color = 0x71f7b5) {
  const radiusX = trackA - 7;
  const radiusZ = trackB - 7;
  const x = Math.cos(angle) * radiusX;
  const z = Math.sin(angle) * radiusZ;
  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(2.8, 2.8, 0.25, 22),
    new THREE.MeshPhongMaterial({
      color,
      emissive: 0x1b4f39,
      shininess: 70,
    }),
  );
  mesh.position.set(x, 0.2, z);
  mesh.receiveShadow = true;
  scene.add(mesh);
  boostPads.push({ x, z, mesh, cooldownMs: 0 });
}

[Math.PI / 5, (2 * Math.PI) / 3, (6 * Math.PI) / 5, (9 * Math.PI) / 5].forEach(
  (a) => createBoostPad(a),
);

function insideTrackBand(x, z) {
  const outerEllipse =
    (x * x) / ((trackA + trackHalfWidth) * (trackA + trackHalfWidth)) +
    (z * z) / ((trackB + trackHalfWidth) * (trackB + trackHalfWidth));
  const innerEllipse =
    (x * x) / ((trackA - trackHalfWidth) * (trackA - trackHalfWidth)) +
    (z * z) / ((trackB - trackHalfWidth) * (trackB - trackHalfWidth));
  return outerEllipse <= 1 && innerEllipse >= 1;
}

function insideTownRoad(x, z) {
  const inTown = x * x + z * z <= 68 * 68;
  const onRoadCross = Math.abs(x) < 8 || Math.abs(z) < 8;
  return inTown && onRoadCross;
}

function getSurfaceType(x, z) {
  if (insideTrackBand(x, z) || insideTownRoad(x, z)) {
    return "Road";
  }
  return "Grass";
}

function getForwardSpeed() {
  const fx = Math.sin(state.yaw);
  const fz = Math.cos(state.yaw);
  return state.vx * fx + state.vz * fz;
}

function updateCheckpointProgress() {
  checkpoints.forEach((cp, idx) => {
    const d = Math.hypot(state.x - cp.x, state.z - cp.z);
    if (d < 7.5) {
      checkpointState[idx] = true;
      cp.ring.material.color.setHex(0x5cf49e);
    }
  });
}

function allCheckpointsHit() {
  for (let i = 0; i < checkpointState.length; i += 1) {
    if (!checkpointState[i]) return false;
  }
  return true;
}

function resetCheckpoints() {
  checkpointState.fill(false);
  checkpoints.forEach((cp, idx) => {
    cp.ring.material.color.setHex(idx === 0 ? 0x5cf49e : 0x5c8ef4);
  });
}

function updatePlayer(dt) {
  const prevX = state.x;
  const prevZ = state.z;

  const steerInput = (input.leftHeld ? 1 : 0) - (input.rightHeld ? 1 : 0);

  const targetThrottle = !input.mapperEnabled
    ? 0
    : input.forwardLatched
      ? 1
      : input.backwardLatched
        ? -1
        : 0;
  input.throttle += (targetThrottle - input.throttle) * Math.min(1, dt * 8);

  const fx = Math.sin(state.yaw);
  const fz = Math.cos(state.yaw);
  const rx = Math.sin(state.yaw + Math.PI / 2);
  const rz = Math.cos(state.yaw + Math.PI / 2);

  const vxLocal = state.vx * fx + state.vz * fz;
  const vyLocal = state.vx * rx + state.vz * rz;
  const speedAbs = Math.abs(vxLocal);

  const steerAngle =
    steerInput *
    (state.maxSteerAngle / (1 + speedAbs * state.steerSpeedFactor));

  const surfaceType = getSurfaceType(state.x, state.z);
  state.surface = surfaceType;
  const cornerStiffFront =
    surfaceType === "Road"
      ? state.cornerStiffFrontRoad
      : state.cornerStiffFrontOffroad;
  const cornerStiffRear =
    surfaceType === "Road"
      ? state.cornerStiffRearRoad
      : state.cornerStiffRearOffroad;
  const tractionLimit =
    surfaceType === "Road"
      ? state.tractionLimitRoad
      : state.tractionLimitOffroad;

  const g = 9.81;
  const loadFront = (state.mass * g * state.rearAxleToCG) / state.wheelBase;
  const loadRear = (state.mass * g * state.frontAxleToCG) / state.wheelBase;

  const eps = 0.5;
  const slipAngleFront =
    Math.atan2(
      vyLocal + state.frontAxleToCG * state.yawVel,
      Math.max(eps, Math.abs(vxLocal)),
    ) -
    Math.sign(vxLocal || 1) * steerAngle;
  const slipAngleRear = Math.atan2(
    vyLocal - state.rearAxleToCG * state.yawVel,
    Math.max(eps, Math.abs(vxLocal)),
  );

  let latForceFront = -cornerStiffFront * slipAngleFront * loadFront;
  let latForceRear = -cornerStiffRear * slipAngleRear * loadRear;
  const maxLatFront = tractionLimit * loadFront;
  const maxLatRear = tractionLimit * loadRear;
  latForceFront = THREE.MathUtils.clamp(
    latForceFront,
    -maxLatFront,
    maxLatFront,
  );
  latForceRear = THREE.MathUtils.clamp(latForceRear, -maxLatRear, maxLatRear);

  let driveForceRear = input.throttle * state.engineForceMax;
  if (input.brakeHeld) {
    driveForceRear += -Math.sign(vxLocal || 1) * state.brakeForceMax;
  }
  if (
    Math.sign(input.throttle) !== Math.sign(vxLocal) &&
    Math.abs(vxLocal) > 1.5
  ) {
    driveForceRear += -Math.sign(vxLocal) * state.brakeForceMax;
  }

  const rolling = state.rollingResistance * vxLocal;
  const drag = state.airDrag * vxLocal * Math.abs(vxLocal);
  let longForce = driveForceRear - rolling - drag;
  const maxLongRear = tractionLimit * loadRear;
  longForce = THREE.MathUtils.clamp(longForce, -maxLongRear, maxLongRear);

  const forceXLocal = longForce - Math.sin(steerAngle) * latForceFront;
  const forceYLocal = latForceRear + Math.cos(steerAngle) * latForceFront;

  const accelXLocal = forceXLocal / state.mass;
  const accelYLocal = forceYLocal / state.mass;

  let nextVxLocal = vxLocal + accelXLocal * dt;
  const nextVyLocal = vyLocal + accelYLocal * dt;
  nextVxLocal = THREE.MathUtils.clamp(
    nextVxLocal,
    state.maxReverseSpeed,
    state.maxForwardSpeed,
  );

  const yawMoment =
    state.frontAxleToCG * Math.cos(steerAngle) * latForceFront -
    state.rearAxleToCG * latForceRear;
  const yawAccel = yawMoment / state.inertia;
  state.yawVel += yawAccel * dt;
  state.yawVel *= Math.max(0.86, 1 - 2.1 * dt);
  state.yaw += state.yawVel * dt;

  state.vx = fx * nextVxLocal + rx * nextVyLocal;
  state.vz = fz * nextVxLocal + rz * nextVyLocal;

  state.x += state.vx * dt;
  state.z += state.vz * dt;

  if (isBlockedByBuilding(state.x, state.z)) {
    state.x = prevX;
    state.z = prevZ;
    state.vx *= -0.22;
    state.vz *= -0.22;
    state.yawVel *= 0.4;
  }

  state.speed = getForwardSpeed();

  const wheelCirc = 2 * Math.PI * state.wheelRadius;
  const targetWheelAV =
    (state.speed / Math.max(0.1, wheelCirc)) * (2 * Math.PI);
  state.wheelAngularVel +=
    (targetWheelAV - state.wheelAngularVel) * Math.min(1, dt * 12);
  state.wheelSpin += state.wheelAngularVel * dt;
  playerWheels.forEach((w) => {
    w.rotation.x = state.wheelSpin;
  });

  playerCar.position.set(state.x, 0, state.z);
  playerCar.rotation.y = state.yaw;

  const camDist = 10;
  camera.position.set(
    state.x - Math.sin(state.yaw) * camDist,
    4.8,
    state.z - Math.cos(state.yaw) * camDist,
  );
  camera.lookAt(state.x, 1.2, state.z);
}

function updateBoostPads(nowMs) {
  for (let i = 0; i < boostPads.length; i += 1) {
    const pad = boostPads[i];
    pad.mesh.rotation.y += 0.02;
    if (nowMs < pad.cooldownMs) continue;

    const d = Math.hypot(state.x - pad.x, state.z - pad.z);
    if (d < 4.2 && Math.abs(state.speed) < state.maxForwardSpeed * 1.05) {
      const fx = Math.sin(state.yaw);
      const fz = Math.cos(state.yaw);
      state.vx += fx * 16;
      state.vz += fz * 16;
      state.score += 75;
      showMessage("BOOST +75", 800);
      pad.cooldownMs = nowMs + 2600;
    }
  }
}

function updateAI(dt) {
  aiCars.forEach((ai) => {
    ai.angle += ai.speed * dt * 60;
    const x = Math.cos(ai.angle) * (trackA - 4);
    const z = Math.sin(ai.angle) * (trackB - 4);
    const nx = Math.cos(ai.angle + 0.02) * (trackA - 4);
    const nz = Math.sin(ai.angle + 0.02) * (trackB - 4);
    ai.mesh.position.set(x, 0, z);
    ai.mesh.lookAt(nx, 0, nz);
    ai.wheelSpin += ai.speed * 30;
    ai.wheels.forEach((w) => {
      w.rotation.x = ai.wheelSpin;
    });
  });
}

function updateLap(nowMs) {
  updateCheckpointProgress();
  const nearStart = Math.abs(state.x - trackA) < 9 && Math.abs(state.z) < 12;
  if (!nearStart) {
    state.canCountLap = true;
  }
  if (
    nearStart &&
    state.canCountLap &&
    Math.abs(state.speed) > 8 &&
    allCheckpointsHit()
  ) {
    const lapMs = nowMs - state.lapStartMs;
    state.lapStartMs = nowMs;
    state.lap += 1;
    state.canCountLap = false;
    state.score += 500;
    resetCheckpoints();

    if (state.bestLapMs === null || lapMs < state.bestLapMs) {
      state.bestLapMs = lapMs;
      showMessage("NEW BEST LAP");
    } else {
      showMessage(`LAP ${state.lap}`);
    }
  }
}

function updatePickups(nowMs) {
  pickups.forEach((pickup) => {
    if (pickup.active) {
      pickup.orb.rotation.y += 0.05;
      pickup.orb.position.y = 1.5 + Math.sin(nowMs * 0.003 + pickup.x) * 0.2;
      const d = Math.hypot(state.x - pickup.x, state.z - pickup.z);
      if (d < 3.2) {
        pickup.active = false;
        pickup.respawnMs = nowMs + 6000;
        pickup.orb.visible = false;
        state.score += 100;
        showMessage("+100");
      }
    } else if (nowMs >= pickup.respawnMs) {
      pickup.active = true;
      pickup.orb.visible = true;
    }
  });
}

function updateHUD(nowMs) {
  const safeSpeed = Number.isFinite(state.speed) ? state.speed : 0;
  const speedKmh = Math.abs(Math.round(safeSpeed * 3.6));
  const rpmValue = 900 + Math.floor(Math.min(6200, Math.abs(safeSpeed) * 65));
  let gear = "N";
  if (safeSpeed > 1) {
    const g = Math.min(6, Math.max(1, Math.ceil(Math.abs(safeSpeed) / 12)));
    gear = String(g);
  } else if (safeSpeed < -1) {
    gear = "R";
  }

  hud.speed.textContent = speedKmh;
  hud.gear.textContent = gear;
  hud.rpm.textContent = String(rpmValue);
  hud.surface.textContent = state.surface;
  hud.lap.textContent = String(state.lap);
  hud.lapTime.textContent = formatMs(nowMs - state.lapStartMs);
  hud.bestTime.textContent =
    state.bestLapMs === null ? "--:--" : formatMs(state.bestLapMs);
  hud.score.textContent = String(state.score);
  hud.mapperState.textContent = input.mapperEnabled ? "ENABLED" : "DISABLED";
  hud.wheelCounter.textContent = input.wheelCounter.toFixed(2);
  hud.wheelAction.textContent = input.forwardLatched
    ? "FORWARD"
    : input.backwardLatched
      ? "BACKWARD"
      : "IDLE";
}

function drawMinimap() {
  mapCtx.clearRect(0, 0, minimap.width, minimap.height);

  mapCtx.fillStyle = "rgba(6, 14, 8, 0.95)";
  mapCtx.fillRect(0, 0, minimap.width, minimap.height);

  const cx = minimap.width / 2;
  const cy = minimap.height / 2;
  const sx = 0.45;
  const sy = 0.62;

  mapCtx.strokeStyle = "#8a8a8a";
  mapCtx.lineWidth = 16;
  mapCtx.beginPath();
  mapCtx.ellipse(cx, cy, trackA * sx, trackB * sy, 0, 0, Math.PI * 2);
  mapCtx.stroke();

  mapCtx.strokeStyle = "#dfdf8f";
  mapCtx.lineWidth = 2;
  mapCtx.beginPath();
  mapCtx.ellipse(
    cx,
    cy,
    ((trackA + trackB) / 2) * sx,
    ((trackA + trackB) / 2) * sy,
    0,
    0,
    Math.PI * 2,
  );
  mapCtx.stroke();

  const px = cx + state.x * sx;
  const pz = cy + state.z * sy;
  mapCtx.fillStyle = "#6ef06e";
  mapCtx.beginPath();
  mapCtx.arc(px, pz, 4, 0, Math.PI * 2);
  mapCtx.fill();

  mapCtx.fillStyle = "#f06e6e";
  aiCars.forEach((ai) => {
    const x = cx + ai.mesh.position.x * sx;
    const z = cy + ai.mesh.position.z * sy;
    mapCtx.beginPath();
    mapCtx.arc(x, z, 3, 0, Math.PI * 2);
    mapCtx.fill();
  });
}

function animate(nowMs) {
  requestAnimationFrame(animate);

  const dt = Math.min(0.05, (nowMs - lastFrameMs) / 1000);
  lastFrameMs = nowMs;

  if (
    !Number.isFinite(state.x) ||
    !Number.isFinite(state.z) ||
    !Number.isFinite(state.vx) ||
    !Number.isFinite(state.vz) ||
    !Number.isFinite(state.yaw)
  ) {
    resetPlayer();
    showMessage("PHYSICS RESET", 900);
  }

  updatePlayer(dt);
  updateAI(dt);
  updateBoostPads(nowMs);
  updatePickups(nowMs);
  updateLap(nowMs);
  updateHUD(nowMs);
  drawMinimap();
  renderer.render(scene, camera);
}

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

showMessage("READY");
animate(performance.now());

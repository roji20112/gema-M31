const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");

canvas.width = 800;
canvas.height = 600;

// السيارة
const car = {
  x: canvas.width / 2,
  y: canvas.height / 2,
  width: 40,
  height: 80,
  angle: 0,
  speed: 0
};

const keys = {};
document.addEventListener("keydown", e => keys[e.key] = true);
document.addEventListener("keyup", e => keys[e.key] = false);

function update() {
  if (keys["ArrowUp"]) car.speed += 0.2;
  if (keys["ArrowDown"]) car.speed -= 0.2;
  if (keys["ArrowLeft"]) car.angle -= 0.05;
  if (keys["ArrowRight"]) car.angle += 0.05;

  // تقليل السرعة تدريجياً
  car.speed *= 0.98;

  // تحديث الموقع
  car.x += Math.sin(car.angle) * car.speed;
  car.y -= Math.cos(car.angle) * car.speed;

  // منع الخروج عن الحدود
  car.x = Math.max(20, Math.min(canvas.width - 20, car.x));
  car.y = Math.max(20, Math.min(canvas.height - 20, car.y));
}

function drawCar() {
  ctx.save();
  ctx.translate(car.x, car.y);
  ctx.rotate(car.angle);
  ctx.fillStyle = "red";
  ctx.fillRect(-car.width / 2, -car.height / 2, car.width, car.height);
  ctx.fillStyle = "black";
  ctx.fillRect(-car.width / 4, -car.height / 2, car.width / 2, 10); // الزجاج الأمامي
  ctx.restore();
}

function drawTrack() {
  ctx.fillStyle = "#444";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 4;
  ctx.setLineDash([20, 20]);
  ctx.beginPath();
  ctx.moveTo(canvas.width / 2, 0);
  ctx.lineTo(canvas.width / 2, canvas.height);
  ctx.stroke();
  ctx.setLineDash([]);
}

function gameLoop() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  drawTrack();
  update();
  drawCar();
  requestAnimationFrame(gameLoop);
}

gameLoop();

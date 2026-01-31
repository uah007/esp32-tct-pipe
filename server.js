const net = require('net');

const LISTEN_PORT = 9000; // Порт, где ESP32 подключается как клиент

// Хранилище параметров от ESP32
let targetEspIP = null;
let targetEspPort = null;
let esp32Socket = null;

const server = net.createServer((socket) => {
  console.log('Новое соединение:', socket.remoteAddress, socket.remotePort);

  if (!esp32Socket) {
    esp32Socket = socket;
    console.log('Целевой IP подключён, ожидаем данные с него');

    let buffer = '';
    const onData = (data) => {
      buffer += data.toString();
      if (buffer.includes('\n')) {
        const line = buffer.trim();
        const parts = line.split(',');
        if (parts.length === 2) {
          targetEspIP = parts[0];
          targetEspPort = parseInt(parts[1], 10);
          console.log(`Получен адрес целевой ESP: ${targetEspIP}:${targetEspPort}`);
          esp32Socket.removeListener('data', onData);
        } else {
          console.log('Ошибка формата данных с ESP32');
          esp32Socket.destroy();
          esp32Socket = null;
          return;
        }
      }
    };

    esp32Socket.on('data', onData);

    esp32Socket.on('close', () => {
      console.log('ESP32 отключён');
      esp32Socket = null;
      targetEspIP = null;
      targetEspPort = null;
    });

    esp32Socket.on('error', (err) => {
      console.error('Ошибка ESP32:', err.message);
      esp32Socket.destroy();
      esp32Socket = null;
      targetEspIP = null;
      targetEspPort = null;
    });

  } else {
    // Подключается браузер или другой клиент
    if (!targetEspIP || !targetEspPort) {
      console.log('Адрес целевой ESP ещё не получен, отклоняем подключение');
      socket.destroy();
      return;
    }

    const targetSocket = net.createConnection({ host: targetEspIP, port: targetEspPort }, () => {
      console.log('Соединение с целевой ESP установлено');
    });

    socket.pipe(targetSocket);
    targetSocket.pipe(socket);

    const closeSockets = () => {
      if (!socket.destroyed) socket.destroy();
      if (!targetSocket.destroyed) targetSocket.destroy();
    };

    socket.on('close', () => {
      console.log('Клиент отключился');
      closeSockets();
    });
    targetSocket.on('close', () => {
      console.log('Целевая ESP отключилась');
      closeSockets();
    });

    socket.on('error', (err) => {
      console.error('Ошибка клиента:', err.message);
      closeSockets();
    });
    targetSocket.on('error', (err) => {
      console.error('Ошибка целевой ESP:', err.message);
      closeSockets();
    });
  }
});

// 🔹 Сигнал Python о готовности
server.listen(LISTEN_PORT, () => {
  console.log(`Сервер TCP запущен на порту ${LISTEN_PORT}`);
  console.log("SERVER_READY"); // <- именно этот сигнал ждет Python
});

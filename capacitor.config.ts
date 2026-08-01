import type { CapacitorConfig } from '@capacitor/cli';

// Hermes Android 一体化 APK:
//   1. APP 启动后加载本地 www/index.html。
//   2. MainActivity 通过 HermesAndroid bridge 提供移动端原生能力。
//   3. 用户不需要安装额外运行环境或执行额外准备步骤。
const config: CapacitorConfig = {
  appId: 'com.sesaloy.hermes',
  appName: '御衡',
  webDir: 'www',
  server: {
    cleartext: true,
    hostname: 'localhost',
    allowNavigation: [
      '127.0.0.1',
      'localhost',
    ],
  },
  android: {
    allowMixedContent: true,
  },
};

export default config;

package com.sesaloy.hermes;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import android.os.PowerManager;

/**
 * 御衡前台服务 — 防止APP被系统后台杀死。
 * 常驻通知 + 活动期间受控WakeLock。
 */
public class KeepAliveService extends Service {

    public static final String CHANNEL_ID = "hermes_keepalive";
    private static final int NOTIF_ID = 1001;
    private PowerManager.WakeLock wakeLock;

    @Override
    public void onCreate() {
        super.onCreate();
        createChannel();
        PowerManager pm = (PowerManager) getSystemService(Context.POWER_SERVICE);
        if (pm != null) {
            // PARTIAL_WAKE_LOCK: 仅在服务存活期间持有，锁屏后CPU仍运行(受控)
            wakeLock = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Hermes:KeepAlive");
            wakeLock.setReferenceCounted(false);
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        startForegroundCompat();
        if (wakeLock != null && !wakeLock.isHeld()) {
            wakeLock.acquire(30 * 60 * 1000L); // 单次最多30分钟，防止常驻耗电
        }
        return START_STICKY; // 被杀后系统尝试重建
    }

    private void startForegroundCompat() {
        Notification notification = buildNotification();
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIF_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC);
        } else {
            startForeground(NOTIF_ID, notification);
        }
    }

    private Notification buildNotification() {
        Intent open = new Intent(this, MainActivity.class);
        PendingIntent pi = PendingIntent.getActivity(
                this, 0, open, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification.Builder b = Build.VERSION.SDK_INT >= 26
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);
        return b
                .setContentTitle("御衡 · 远程驾驶舱")
                .setContentText("服务运行中，随时接收指令")
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pi)
                .setOngoing(true)
                .setPriority(Notification.PRIORITY_LOW) // 低调常驻
                .build();
    }

    private void createChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            NotificationChannel ch = new NotificationChannel(
                    CHANNEL_ID, "御衡后台服务",
                    NotificationManager.IMPORTANCE_MIN); // 最低打扰
            ch.setDescription("保持APP后台存活，接收远程指令");
            NotificationManager nm = getSystemService(NotificationManager.class);
            if (nm != null) nm.createNotificationChannel(ch);
        }
    }

    @Override
    public void onDestroy() {
        if (wakeLock != null && wakeLock.isHeld()) {
            wakeLock.release();
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}

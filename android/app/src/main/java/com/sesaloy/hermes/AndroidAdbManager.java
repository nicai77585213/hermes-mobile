package com.sesaloy.hermes;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;

final class AndroidAdbManager {
    private static final int DEFAULT_TIMEOUT_SECONDS = 20;
    private final Context context;

    AndroidAdbManager(Context context) {
        this.context = context.getApplicationContext();
    }

    JSONObject status() {
        JSONObject result = run(DEFAULT_TIMEOUT_SECONDS, null, "devices", "-l");
        JSONArray devices = new JSONArray();
        String output = result.optString("output", "");
        for (String line : output.split("\\r?\\n")) {
            String trimmed = line.trim();
            if (trimmed.isEmpty() || trimmed.startsWith("List of devices")) {
                continue;
            }
            String[] parts = trimmed.split("\\s+", 2);
            JSONObject device = new JSONObject();
            try {
                device.put("serial", parts[0]);
                device.put("state", parts.length > 1 ? parts[1] : "unknown");
                devices.put(device);
            } catch (Exception ignored) {
            }
        }
        try {
            result.put("devices", devices);
            boolean hasReadyDevice = false;
            for (int i = 0; i < devices.length(); i++) {
                if ("device".equalsIgnoreCase(devices.getJSONObject(i).optString("state"))) {
                    hasReadyDevice = true;
                    break;
                }
            }
            result.put("connected", hasReadyDevice);
        } catch (Exception ignored) {
        }
        return result;
    }

    JSONObject pair(String host, int port, String code) {
        return run(25, code == null ? "" : code.trim(), "pair", endpoint(host, port));
    }

    JSONObject connect(String host, int port) {
        JSONObject result = run(DEFAULT_TIMEOUT_SECONDS, null, "connect", endpoint(host, port));
        try {
            String output = result.optString("output", "").toLowerCase();
            result.put("connected", result.optInt("exitCode", -1) == 0 && (output.contains("connected to") || output.contains("already connected")));
        } catch (Exception ignored) {
        }
        return result;
    }

    JSONObject shell(String serial, String command) {
        List<String> args = new ArrayList<>();
        if (serial != null && !serial.trim().isEmpty()) {
            args.add("-s");
            args.add(serial.trim());
        }
        args.add("shell");
        args.add(command == null ? "" : command);
        return run(60, null, args.toArray(new String[0]));
    }

    private JSONObject run(int timeoutSeconds, String stdin, String... args) {
        JSONObject result = new JSONObject();
        Process process = null;
        StringBuilder output = new StringBuilder();
        try {
            List<String> command = new ArrayList<>();
            command.add(adbExecutable().getAbsolutePath());
            command.addAll(Arrays.asList(args));
            ProcessBuilder builder = new ProcessBuilder(command);
            builder.directory(context.getFilesDir());
            builder.redirectErrorStream(true);
            builder.environment().put("HOME", context.getFilesDir().getAbsolutePath());
            builder.environment().put("TMPDIR", context.getCacheDir().getAbsolutePath());
            process = builder.start();
            if (stdin != null) {
                PrintWriter writer = new PrintWriter(new OutputStreamWriter(process.getOutputStream(), StandardCharsets.UTF_8), true);
                writer.println(stdin);
                writer.flush();
            }
            final Process runningProcess = process;
            Thread reader = new Thread(() -> {
                try (BufferedReader buffered = new BufferedReader(new InputStreamReader(runningProcess.getInputStream(), StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = buffered.readLine()) != null) {
                        if (output.length() < 32768) {
                            output.append(line).append('\n');
                        }
                    }
                } catch (Exception ignored) {
                }
            }, "hermes-adb-output");
            reader.start();
            boolean finished = process.waitFor(timeoutSeconds, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                process.waitFor(3, TimeUnit.SECONDS);
            }
            reader.join(1500);
            result.put("ok", finished && process.exitValue() == 0);
            result.put("exitCode", finished ? process.exitValue() : -1);
            result.put("timedOut", !finished);
            result.put("output", output.toString().trim());
        } catch (Exception error) {
            try {
                result.put("ok", false);
                result.put("exitCode", -1);
                result.put("error", error.getClass().getSimpleName() + ": " + error.getMessage());
                result.put("output", output.toString().trim());
            } catch (Exception ignored) {
            }
        } finally {
            if (process != null) {
                process.destroy();
            }
        }
        return result;
    }

    private File adbExecutable() {
        return new File(context.getApplicationInfo().nativeLibraryDir, "libadb_exec.so");
    }

    private static String endpoint(String host, int port) {
        String safeHost = host == null || host.trim().isEmpty() ? "127.0.0.1" : host.trim();
        if (safeHost.contains(":")) {
            safeHost = "[" + safeHost.replace("[", "").replace("]", "") + "]";
        }
        return safeHost + ":" + port;
    }
}

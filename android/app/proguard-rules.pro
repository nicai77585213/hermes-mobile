# Hermes Mobile ProGuard/R8 规则
# 关键：Python-Java 桥、WebView JS 接口、反射调用的类必须保留

# Chaquopy: Python 通过 JNI 反射调用 Java 类，禁止混淆/裁剪
-keep class com.chaquo.python.** { *; }
-keep class com.chaquo.python.android.** { *; }

# Capacitor 桥
-keep class com.getcapacitor.** { *; }
-keep class com.getcapacitor.plugin.** { *; }

# 本项目入口与内部桥（Python 会反射调用）
-keep class com.sesaloy.hermes.** { *; }

# WebView JavaScript 接口：JS 端通过名字调用，方法必须保留原名
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
-keepattributes JavascriptInterface
-keepattributes *Annotation*

# 反射/序列化保留
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations

# Chaquopy 动态导入的 Python 模块引用
-dontwarn com.chaquo.python.**
-dontwarn com.getcapacitor.**
-dontwarn org.json.**

# 保留行号便于排障（release 版）
-keepattributes SourceFile, LineNumberTable

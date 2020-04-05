---
layout: post
title:  'A Little Notes: About ClassLoader'
date:   2020-04-05 16:42:34 +0800
author: dox4
categories: notes
tags: Java, ClassLoader
---


To understand *How Tomcat Works*, record a little notes about ClassLoader in Java.

---

*How Tomcat Works* 一书中的代码，在最初介绍 `Servlet` 服务器的时候就引入了 `URLClassLoader` 类，于是顺便了解了一下 `Java` 中的类加载器。

在 `JVM` 中内置了三个类加载器，分别是：
- 负责加载运行时需要的核心类的 `BootstrapClassLoader` ，这个类加载器直接内置在 `JVM` 中，根据 `JVM` 的不同，由 `C/C++` 实现；
- 加载 `JVM` 扩展类的 `ExtClassLoader`；
- 和负责加载用户程序的 `AppClassLoader`。

后两者都是 `sun.misc.Launcher` 的静态内部类。

通过该类的源码可以看到（反编译得到，可能有版权问题？）：
```Java
public Launcher() {
    Launcher.ExtClassLoader var1;
    try {
        var1 = Launcher.ExtClassLoader.getExtClassLoader();
    } catch (IOException var10) {
        throw new InternalError("Could not create extension class loader", var10);
    }

    try {
        this.loader = Launcher.AppClassLoader.getAppClassLoader(var1);
    } catch (IOException var9) {
        throw new InternalError("Could not create application class loader", var9);
    }
...
}
```

先是得到了一个 `ExtClassLoader`，然后将其作为参数传递给了 `AppClassLoader`。

## ExtClassLoader

构造 `ExtClassLoader` 的源码：
```Java
public static Launcher.ExtClassLoader getExtClassLoader() throws IOException {
    if (instance == null) {
        Class var0 = Launcher.ExtClassLoader.class;
        synchronized(Launcher.ExtClassLoader.class) {
            if (instance == null) {
                instance = createExtClassLoader();
            }
        }
    }
    return instance;
}
private static Launcher.ExtClassLoader createExtClassLoader() throws IOException {
    try {
        return (Launcher.ExtClassLoader)AccessController.doPrivileged(new PrivilegedExceptionAction<Launcher.ExtClassLoader>() {
            public Launcher.ExtClassLoader run() throws IOException {
                File[] var1 = Launcher.ExtClassLoader.getExtDirs();
                ...
                return new Launcher.ExtClassLoader(var1);
            }
        });
    } catch (PrivilegedActionException var1) {
        throw (IOException)var1.getException();
    }
}
 private static File[] getExtDirs() {
    String var0 = System.getProperty("java.ext.dirs");  // here
    ...
 }
 ```
 可以看到通过 `java.ext.dirs` 获得了扩展类所在的目录。

## AppClassLoader

 `AppClassLoader` 的构造要简单很多：
 ```Java
 public static ClassLoader getAppClassLoader(final ClassLoader var0) throws IOException {
    final String var1 = System.getProperty("java.class.path");
    final File[] var2 = var1 == null ? new File[0] : Launcher.getClassPath(var1);
    return (ClassLoader)AccessController.doPrivileged(new PrivilegedAction<Launcher.AppClassLoader>() {
        public Launcher.AppClassLoader run() {
            URL[] var1x = var1 == null ? new URL[0] : Launcher.pathToURLs(var2);
            return new Launcher.AppClassLoader(var1x, var0);
        }
    });
}
```
通过 `java.class.path` 来获得用户应用程序所在的目录加载对应的类。

## 委托关系和继承关系

每个 `ClassLoader` 都有一个 `parent` 成员，作为自己的上级 `ClassLoader` （区别于**父类**）。

`AppClassLoader` 的 `parent` 成员是 `ExtClassLoader`，这一点也可以通过追踪源码得到，不过调用层级有点多。下方的代码可以更简单地验证这一点。

`ExtClassLoader` 的 `parent` 成员是空的，所以它的父加载器是**根加载器**，也就是由 `JVM` 提供的那一个。

 `sum.misc.Launcher$ExtClassLoader` 和 `sum.misc.Launcher$AppClassLoader` 的父类都是 `URLClassLoader`，可以通过反编译源码得到，也可以通过下方的代码。

```Java
ClassLoader cl = Thread.currentThread().getContextClassLoader();
System.out.println(Thread.currentThread().getId() + ": " + cl);
while (cl != null) {
    System.out.println(cl.getClass().getCanonicalName());
    System.out.println("\t" + cl.getClass().getSuperclass().getCanonicalName());
    cl = cl.getParent();
}
```

输出为：
```
sun.misc.Launcher.AppClassLoader
	java.net.URLClassLoader
sun.misc.Launcher.ExtClassLoader
	java.net.URLClassLoader
```

## AppClassLoader 是全局的

直接上代码吧。
```Java
for (int i = 0; i < 10; i++) {
    Thread thread = new Thread(){
        @Override
        public void run() {
            super.run();
            System.out.println(Thread.currentThread().toString() + 
                Thread.currentThread().getContextClassLoader());
        }
    };
    thread.start();
}
```
输出：
```
Thread[Thread-0,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-1,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-2,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-3,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-4,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-5,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-6,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-7,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-9,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
Thread[Thread-8,5,main]sun.misc.Launcher$AppClassLoader@18b4aac2
```

不仅看到了不同线程的 `AppClassLoader` 是同一个，还偶然看到了 `JVM` 中线程的乱序执行。
---
layout: post
title:  让 Servlet 跑起来的最小代码（不使用 Tomcat）
date:   2020-03-14 01:02:01 +0800
author: dox4
categories: notes development
tags: servlet, web development, Java
---

理了一下让 Servlet 跑起来的方法。

---

## Tomcat

Tomcat 是一个著名的 Web 容器。至于容器究竟是什么，似乎不太容易在一篇文章里说明白，也不是这篇文章的主题。

不过我还是简单说一下我的理解。

Servlet 这个词的含义是 **Server Applet**，意即服务端小程序。而且 Servlet 本身结构很简单，虽然 `service` 方法可以把服务器上所有的事情都处理了，但显然这么做并不明智。

使用 Tomcat 这类容器的通行做法，则是在程序中编写多个 Servlet，分别负责不同的功能，来处理不同的网络请求。Tomcat 则更多地扮演着“**Servlet 管理者**”的身份，这应该也就是 **Web 容器**所做的事情吧。

## 使用 Tomcat

使用 Tomcat 的教程网上有一堆，我就不多赘述了。

其中最关键的一步是这样的。

假设我们编写了一个 Servlet：
```Java
package dox4.sparrow;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * @author dox
 */
public class A1Servlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        PrintWriter writer = resp.getWriter();
        writer.println("This is an A1 Servlet response.");
        writer.close();
    }
}
```

（这里我只覆盖了 `doGet` 方法，毕竟只是一个示例。）

然后需要在 `web.xml` 中配置这个 Servlet。
```xml
<web-app>      
    <servlet>
        <servlet-name>A1</servlet-name>
        <servlet-class>dox4.sparrow.A1Servlet</servlet-class>
    </servlet>
    <servlet-mapping>
        <servlet-name>A1</servlet-name>
        <url-pattern>/A1</url-pattern>
    </servlet-mapping>
</web-app>  
```
这样我们使用 `GET` 方法请求 `http://hostname:port/url-prefix/A1` 的时候，就会得到
```
This is an A1 Servlet response.
```
的信息了。

按照这个写法，它的逻辑应该是这样的：

Tomcat 启动的时候解析 `web.xml` 文件，对 `<servlet-mapping>` 标签进行分析和记录，可以列出这个服务器所有可以接受的请求路径；对 `<servlet>` 标签分析和记录，可以列出这个服务器所有的 Servlet 服务。请求路径和 Servlet 应该一一对应。当然多个请求对应一个 Servlet 也不会有什么问题，反之则不然。

当一个请求被 Tomcat 接收的时候，它去分析 Request 中的 `URI`，然后去找到对应的 Servlet，如果没有找到就返回 `404 Not Found`。找到了则实例化对应的 Servlet，并调用它的 `service` 方法。

等 Servlet 的 `service` 方法返回之后，再进行一些收尾的工作，比如关闭输出流什么的。

这大概就是 Tomcat 的**最简**工作流程了，实际情况肯定会比这个复杂。

## 最简单的 Servlet 管理器

在[上一篇文章](/notes/development/2020/03/12/%E5%A4%8D%E4%B9%A0%E4%B8%80%E4%B8%8B-Socket.html)中，我写了一个最简单的服务器，现在把这个服务器改造一下，让它能“动态”地调用 Servlet 来处理请求。

要想自己调用 Servlet，还有一个前提，就是需要 `HttpServletRequest` 和 `HttpServletResponse` 这两个接口的实现类。

使用 Tomcat 时，可以直接使用它提供的实现类，如果想要不依赖 Tomcat 把 Servlet 跑起来，这两个实现类就得自己写了。

当然作为一个示例，只需要实现一点点功能就可以了。

`HttpServletRequest` 最少要实现的其实只有一个方法，就是 `getMethod()`。这是因为在调用 `HttpServlet` 中的 `service()` 方法的时候，要用到这个方法。

`HttpServlet` 中的 `service()` 方法源码如下：

```Java
@Override
public void service(ServletRequest req, ServletResponse res)
    throws ServletException, IOException
{
    HttpServletRequest  request;
    HttpServletResponse response;
    
    if (!(req instanceof HttpServletRequest &&
            res instanceof HttpServletResponse)) {
        throw new ServletException("non-HTTP request or response");
    }

    request = (HttpServletRequest) req;
    response = (HttpServletResponse) res;

    service(request, response);
}
```

可以看到在这个方法的最后，请求被强转后转发给了另外一个 `service()` 方法，转发后 `service()` 方法的部分源码：

```java
protected void service(HttpServletRequest req, HttpServletResponse resp)
    throws ServletException, IOException
{
    String method = req.getMethod();

    if (method.equals(METHOD_GET)) {
        long lastModified = getLastModified(req);
        if (lastModified == -1) {
            // servlet doesn't support if-modified-since, no reason
            // to go through further expensive logic
            doGet(req, resp);
        } else {
...
            
```

这个方法的基本逻辑就是按照 Request 的类型不同而分别调用对应的 `doMethod()` 方法，所以**不建议重写**这个方法。它获得请求类型使用的是 `getMethod()`，所以对于 `HttpServletRequest` 的实现类来说，这个方法是唯一**必须**要实现的。作为是最简单的示例，可以直接返回 `"GET"` 字面值。

其他的方法随便返回 `null` 之类的可以通过编译就好了。

`HttpServletResponse` 最少要实现的也只有一个方法，不过为了实现这个方法，需要给它加一个成员变量。

在最简单的服务器中，给客户端返回信息使用的是 `socket` 的输出流，但是在 `HttpServeltResponse` 中并没有这个输出流，它有一个 `getOutputStream()` 的方法，但返回类型是 `ServletOutputStream`，而不是 `SocketOutputStream`。

在上边的 `A1Servlet` 示例中，给客户端返回信息使用的是 `getWriter()`，此方法的返回值类型为 `PrintWriter`。

`PrintWriter` 可以通过提供一个 `OutputStream` 类型的参数构造，从而方便地向其中写入信息。

因而可以把 `socket.getOutputStream()` 作为参数来构造对应的 `PrintWriter` 供 `getWriter()` 返回：

```Java
// part of class SimpleResponse

// member of SimpleResponse,
// to bind the SocketOutputStream from socket
private OutputStream output;

// constructor, accept a OutputStream
SimpleResponse(OutputStream output) {
    this.output = output;
}
// return the writer
@Override
public PrintWriter getWriter() throws IOException {
    if (output == null) {
        throw new IOException();
    }
    return new PrintWriter(output);
}
```

当然也可以直接将类成员的类型改为 `PrintWriter`：
```Java
// part of class SimpleResponse

// member of SimpleResponse,
// to bind the SocketOutputStream from socket
private PrintWriter writer;

// constructor, accept an OutputStream
SimpleResponse(OutputStream output) {
    this.writer = new PrintWriter(output);
}

// return the writer
@Override
public PrintWriter getWriter() throws IOException {
    return writer;
}
```

后边这种写法有一个好处就是可以：

```Java
resp.getWriter().println("...");    // wrtie the response info
resp.getWriter().close();           // close the output stream
```

如果使用前一种写法，在 `close()` 那一步调用的 `getWriter()` 返回的是一个新的 `PrintWriter` 对象，不能把写入信息的 `PrintWriter` 对象关闭。

现在，请求和响应都有了，就可以着手对 Servlet 进行管理了。

仿照上边的 `A1Servlet`，再新建一个 `A2Servlet`。用这两个 Servlet 作为管理对象：

```Java
// get the IO stream from socket
InputStream input = socket.getInputStream();
OutputStream output = socket.getOutputStream();
// build the request and response
SimpleRequest request = new SimpleRequest(input);
SimpleResponse response = new SimpleResponse(output);
// dispatch the request to corresponding servlet
switch (request.getRequestURI()) {
    case "/A1":
        new A1Servlet().service(request, response);
        break;
    case "/A2":
        new A2Servlet().service(request, response);
        break;
    default:
        output.write("Your request path is no servlet configured.".getBytes());
        break;
}
```

这个“管理”非常（× 10010）简陋。

但它确实做到了“**根据请求路径调用对应的服务**”这件事，这也是容器所要达成的最根本的任务。

本文所示代码在 [sparrow-0.0.2](https://github.com/dox4/sparrow/tree/0.0.2) 项目分支。
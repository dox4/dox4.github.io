---
layout: post
title: 多个 Github 账号的 ssh-key 配置方法
date: 2020-03-01 01:09:17 +0800
author: dox4
categories: notes memo
tags: Github, ssh-key
---

其实加个配置文件就行了。

因为新建这个博客，所以我遇到了要在一台电脑上登录两个 Github 账号的问题，申请两个账号很容易，但管理起来就不是那么顺畅了。

## Generate more SSH-Keys

每个 ssh-key 只能对应一个 Github 账号，所以就需要两个 ssh-key。生成两个 ssh-key 倒是简单，在

```
ssh-keygen -t rsa -C "your email address"
```

的时候，是可以输入文件名的，这样在 `~/.ssh` 目录下就可以有复数对公钥和私钥文件。类似这样（ `ls` 的结果）：

```
Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-a----         2020/2/28    21:44            246 config
-a----         2020/2/25    21:44           3243 id_rsa
-a----         2020/2/25    21:44            748 id_rsa.pub
-a----         2020/2/28    21:30           3243 id_rsa_dox4
-a----         2020/2/28    21:30            744 id_rsa_dox4.pub
-a----         2020/2/26    22:08           1589 known_hosts
```

## Configure SSH-Keys

将公钥添加到对应的 Github 账号中，就可以使用了……并不。因为 git 会默认使用文件名为 id_rsa 的那一对公钥和私钥，所以对于不是这个名字的公钥和私钥就需要个别的设置，这就用到了
```
~/.ssh/config # create if not exist
```
文件。

我的这个文件中的内容大致如下：
```
Host github.com
  HostName github.com
  User git
  IdentityFile /path/to/.ssh/id_rsa
Host dox4.github.com
  HostName github.com
  User git
  IdentityFile /path/to/.ssh/id_rsa_dox4
```
所谓的 Host 并不是真的主机，只不过是对下边的 HostName 取了个别名，用来区分不同的配置文件。

## Configure repo

这个配置文件是给 `git` 使用的。所以也要改动对应的 Github 账号下边的 repo 的配置文件。

```
# part of /repodir/.git/config
...
[remote "origin"]
    #   modify this line:
	url = git@github.com:dox4/repo-name.git
    #   to:
	url = git@dox4.github.com:dox4/repo-name.git
	fetch = +refs/heads/*:refs/remotes/origin/*
...
```

### Test

设置完成后，可以通过 `ssh` 命令测试一下，例如：
```
ssh -T dox4.github.com
```
如果得到了类似以下信息的回应：
```
Hi dox4! You've successfully authenticated, but GitHub does not provide shell access.
```
就说明配置成功了。

---
### ~~没有什么用的豆知识~~

我试着 `ping` 了几个类似 `xxxx.github.com` 的子域名，都会被转发到 `github.github.io`。
```
> ping dox4.github.com

正在 Ping github.github.io [185.199.110.153] 具有 32 字节的数据:
来自 185.199.110.153 的回复: 字节=32 时间=104ms TTL=51
...

> ping hdihdheidwhweifuwef.github.com

正在 Ping github.github.io [185.199.109.153] 具有 32 字节的数据:
来自 185.199.109.153 的回复: 字节=32 时间=68ms TTL=51
...
```
---
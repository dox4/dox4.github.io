---
layout: post
title:  A little trap in Date in Excel
date:   2020-10-22 16:30:04 +0800
author: dox4
categories: notes
tags: POI, Java, Date, Excel
---

At first, let's see the minimal code to jump into this trap.

## repetition

This trap is about Excel, so we should have an Excel file, and then, let's write a number `44125.0729162616` in the first cell.

> note: `44125.0729162616` is NOT the only particular number.

Next, change the format of the cell to a date type that has both date part and time part, for example, `yyyy/mm/dd hh:mm:ss`.

If you used the number and format above, you would see `2020/10/21 01:45:00`, or an equivalent date string, remember it.

## read the date with Java

The most popular libarary to read Excel with Java is `Apache POI`, so add the dependency:
```xml
<dependency>
    <groupId>org.apache.poi</groupId>
    <artifactId>poi-ooxml</artifactId>
    <version>4.1.2</version>
</dependency>
```

Now we can read the Excel that has the only value.

```Java
public class DateInExcel {
    public static void main(String[] args) throws IOException {
        Workbook wb = new XSSFWorkbook("date-in-excel.xlsx");
        Cell cell = wb.getSheetAt(0).getRow(0).getCell(0);
        DateFormat df = new SimpleDateFormat("yyyy/MM/dd HH:mm:ss");
        System.out.println(df.format(cell.getDateCellValue()));
    }
}
```

Here's the value shown in console:
```plaintext
2020/10/21 01:44:59
```

Okay, we're in the trap.

We have `2020/10/21 01:45:00` but we get `2020/10/21 01:44:59`, why do we lose one second?

## dates in Excel

To make it clear why we lost one second, we should figure out that how the date value is stored in Excel.

As we have done at the beginning, we wrote a **number** in the cell, so it is obvious that dates in Excel are numeric. In fact,
almost in every programming language, `Date` is number.

In Excel, a single day is represented by the integer part of a decimal number, and the hours, minutes and the more detailed time parts are represented by the fraction part.

Let's look back at the number above, `44125.0729162616`.

The integer part is `44125`, in Excel, the first day of dates is `1900/01/01`, you can put an `1` in a cell and format it as date type, you'll get `1900/01/01`.

So as we put `44125` and get `2020/10/21`.

> note: if you calculate how many days it is from `1900/01/01` to `2020/10/21`, you will get `44123`, rather than `44124`(`44125 - 1`). This is about a `bug-is-feature` story, which is not we focus on in this post. In short to say, `1900/02/29` is a valid date in Excel which is actually not.

## truth of the trap

You might have got the point.

Number is based on `10` while the time (minute to hour, second to minute) is based on `60`. So **NOT** every time point in a day has an exact representation with decimal number.

We could calculate it.

A day has 24 hours, an hour has 60 minutes..., and a day has `24 * 60 * 60 = 86400` seconds.

So we have `86400 * 0.0729162616 = 6299.96500224` seconds, while one hour and `45` minutes is `6300` seconds.

We got it, `44125.0729162616` in Excel actually is not `2020/10/21 01:45:00`, they have almost `35` milliseconds in difference.

To prove it again, we change the format in Java to `yyyy/MM/dd HH:mm:ss.SSS`, then we see `2020/10/21 01:44:59.965`, that matches the result we calculate above.

The reason indicates that, `44125.0729162616` is not the only case that has difference between the representations by Excel and `Apache POI` with the same value. We can construct a lot values that make these differences.

So let me leave a question here: how to figure out the boundry to change the representation from this second to next in Excel?

## solution or what we want

If we need to import Excel files in our program, we may not ask for a precise time point in milliseconds. Actually, in our business, second is usually the minimal time unit.

There is a little trick to avoid getting the wrong time value while encountering these weird inputs, add `500` milliseconds on the value from Excel.

You might know this is the common way for rouding a number. And in the source code of `Apache POI`, there is a method:
```Java
// class org.apache.poi.ss.usermodel.DateUtil
public static Date getJavaDate(double date, boolean use1904windowing, TimeZone tz, boolean roundSeconds);
```

The last parameter `roundSeconds` is a boolean value used to prompt whether rounding seconds or not.

But this method is not easy to use, 'cause you must get the decimal value of the cell and the boolean value that indicates whether the date systems used in the workbook starts in 1904 by yourself.

To get the second boolean value, you must make sure the workbook is an instance of `class XSSFWorkbook`, and then get it by `XSSFWorkbook.isDate1904()`.

So what I recommend is just getting the date value, and then adding `500` milliseconds.
```Java
Date date = new Date(cell.getDateCellValue().getTime() + 500);
```

## some nonsense

At last, honest to say, this is the very first time I wrote a post in English. If there are any errors or omissions, please be tolerant ;).
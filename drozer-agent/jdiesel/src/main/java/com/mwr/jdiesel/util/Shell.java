package com.mwr.jdiesel.util;

import android.util.Log;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;


public class Shell {
	
	private Process fd = null;
	private int[] id = new int[1];
	InputStream stdin = null;
	InputStream stderr = null;
	OutputStream stdout = null;
	
	public Shell() throws IOException, InterruptedException {
		this.fd = Runtime.getRuntime().exec("/system/bin/sh -i");
		this.stdin = this.fd.getInputStream();
		this.stderr = this.fd.getErrorStream();
		this.stdout = this.fd.getOutputStream();
		this.write(String.format("cd %s", System.getProperty("user.dir")));
		this.read();
		
	}
	
    public void close() {
    	this.fd.destroy();
    }

	public String read() throws IOException, InterruptedException {
		StringBuffer value = new StringBuffer();
		
		while(this.stdin.available() > 0) {
			for(int i=0; i<this.stdin.available(); i++) {
				int c = this.stdin.read();

				value.append((char)c);
			}
			
			Thread.sleep(15);
		}
		while(this.stderr.available() > 0) {
			for(int i=0; i<this.stderr.available(); i++) {
				int c = this.stderr.read();

				value.append((char)c);
			}
			
			Thread.sleep(15);
		}

		return value.toString();
	}
	
	public boolean valid() {

			try{
				this.fd.exitValue();
				return false;
			}catch(IllegalThreadStateException e){
				return true;
			}
			
			/*
		try{
			Runtime run = Runtime.getRuntime();
			Process pr = run.exec("ps " + this.id[0]);
			pr.waitFor();
			
			BufferedReader buf = new BufferedReader(new InputStreamReader(pr.getInputStream()));
			String line = "";
			while((line=buf.readLine()) != null) {
				if(line.contains("" + this.id[0])) {
					if(line.split("\\s+")[7].equals("Z"))
						return true;
				}
			}
			
		}
		catch(IOException e) {Log.e("JDIESEL : SHELL", String.format("IO ERROR: %s", e.getMessage()));}
		catch (InterruptedException e) {Log.e("JDIESEL : SHELL", String.format("INTERRUPTED ERROR: %s", e.getMessage()));}
		
		return true;
		*/
	}
    public void write(String value) throws IOException, InterruptedException {
    	this.stdout.write((value + "\n").getBytes());
		this.stdout.flush();
		Thread.sleep(100);

	}

	/**
	 * 执行 adb 命令
	 *
	 * @param cmd 命令
	 * @return
	 */
	public static StringBuffer shellExec(String cmd) {
		Runtime mRuntime = Runtime.getRuntime(); //执行命令的方法
		try {
			//Process中封装了返回的结果和执行错误的结果
			Process mProcess = mRuntime.exec(cmd); //加入参数
			//使用BufferReader缓冲各个字符，实现高效读取
			//InputStreamReader将执行命令后得到的字节流数据转化为字符流
			//mProcess.getInputStream()获取命令执行后的的字节流结果
			BufferedReader mReader = new BufferedReader(new InputStreamReader(mProcess.getInputStream()));
			//实例化一个字符缓冲区
			StringBuffer mRespBuff = new StringBuffer();
			//实例化并初始化一个大小为1024的字符缓冲区，char类型
			char[] buff = new char[1024];
			int ch = 0;
			//read()方法读取内容到buff缓冲区中，大小为buff的大小，返回一个整型值，即内容的长度
			//如果长度不为null
			while ((ch = mReader.read(buff)) != -1) {
				//就将缓冲区buff的内容填进字符缓冲区
				mRespBuff.append(buff, 0, ch);
			}
			//结束缓冲
			mReader.close();
			//Log.i("shell", "shellExec: " + mRespBuff);
			//弹出结果
//            Log.i("shell", "执行命令: " + cmd + "执行成功");
			return mRespBuff;

		} catch (IOException e) {
			// 异常处理
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		return null;
	}
    
}

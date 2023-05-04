package com.mwr.dz;

import android.app.Application;
import android.content.Context;
import android.util.Log;

public class DrozerApplication extends Application {
    public static Context sAppliton = null;
    @Override
    public void onCreate() {

        super.onCreate();
        sAppliton = this.getApplicationContext();
    }
}

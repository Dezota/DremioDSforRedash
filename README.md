![image](https://github.com/Dezota/dockerfiles/raw/master/dezota_logo_sm.png)

# Dremio Data Source Driver for Redash.io

This is a [Redash](https://github.com/getredash/redash) data source driver that support Dremio Server. The best way to try it out is to use the [Dezota Redash Docker Image](https://hub.docker.com/r/dezota/redash/). More details on the image and its associated Docker Compose files can be found [here](https://github.com/Dezota/dockerfiles/tree/master/redash).

For more details and documentation on Redash go to their [website](https://www.redash.io/).
For more details and documentation on Dremio go to their [website](https://www.dremio.com/).

### Install the Driver into Redash.io
#### Run this for an existing instance if you aren't using our custom Docker image
```
wget -O - https://raw.githubusercontent.com/Dezota/DremioDSforRedash/master/install_ubuntu.sh | bash
```

### Get started
![image](https://github.com/Dezota/DremioDSforRedash/raw/master/dremio_odbc_newds.jpg)

If you have installed everything correctly, you should now see the Dremio datasource.

![image](https://github.com/Dezota/DremioDSforRedash/raw/master/dremio_odbc_settings.jpg)

You must enter the data source name, server, username, and password.  Enjoy!

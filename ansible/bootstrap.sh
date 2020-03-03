#!/bin/sh

# specify build dir for release branch here.
BUILD_DIR=/auto/nmtg-hudson2-gpk/cdimages/lnx_cpo_franklin_rib/daily/LNX_CPO_FRANKLIN_RIB_LATEST

# create ansible inventory file
ANSIBLE_CFG_DIR=~/etc/lazyjack
if [ -d $ANSIBLE_CFG_DIR ]; then
    echo "If you want a new release of 'CI scripts' remove ~/etc/lazyjack"
    echo "Nothing to do, exiting..."
    exit 0
fi
mkdir -p $ANSIBLE_CFG_DIR
echo "[devservers]" > $ANSIBLE_CFG_DIR/hosts
echo `hostname` >> $ANSIBLE_CFG_DIR/hosts
echo "" >> $ANSIBLE_CFG_DIR/hosts
echo "[local]" >> $ANSIBLE_CFG_DIR/hosts
echo "localhost" >> $ANSIBLE_CFG_DIR/hosts
echo "" >> $ANSIBLE_CFG_DIR/hosts
echo "[all:vars]" >> $ANSIBLE_CFG_DIR/hosts
echo "ansible_python_interpreter=/sw/packages/python/2.7.1/bin/python" >> $ANSIBLE_CFG_DIR/hosts
echo "launch_dir=/data/cdimage/Disk1" >> $ANSIBLE_CFG_DIR/hosts
echo "nfs_dir=$BUILD_DIR" >> $ANSIBLE_CFG_DIR/hosts
echo "target_build_dir=/data/cdimage" >> $ANSIBLE_CFG_DIR/hosts
echo "target_inst_dir=/cisco/PrimeOpticalServer" >> $ANSIBLE_CFG_DIR/hosts
echo "view_build_dir=/vob/visionway/ctm/server/release/cdimage/Disk1" >> $ANSIBLE_CFG_DIR/hosts

# copy playbooks
cp *.yml $ANSIBLE_CFG_DIR
# copy the script (the red button)
cp install.py $ANSIBLE_CFG_DIR
cp install.sh $ANSIBLE_CFG_DIR
cp "test.sh" $ANSIBLE_CFG_DIR
# copy the response file template
mkdir -p $ANSIBLE_CFG_DIR/templates
cp templates/*.j2 $ANSIBLE_CFG_DIR/templates
# copy tasks dir
mkdir -p $ANSIBLE_CFG_DIR/tasks
cp tasks/*.yml $ANSIBLE_CFG_DIR/tasks

# create SSH keypair
KEY_ID=ci_rsa
if [ ! -f ~/.ssh/$KEY_ID ]; then
    echo "Please do not add a passphrase if you plan to use the install script in crontab."
    echo "just press enter twice"
    ssh-keygen -f ~/.ssh/$KEY_ID
    # install SSH public key for user
    touch ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    cat ~/.ssh/$KEY_ID.pub >> ~/.ssh/authorized_keys
fi

# install SSH public key for root
res=`sudo grep -l $USER /root/.ssh/authorized_keys`
if [ "$?" -ne "0" ]; then
    cp ~/.ssh/$KEY_ID.pub /tmp
    sudo /bin/sh -c "cat /tmp/$KEY_ID.pub >> /root/.ssh/authorized_keys"
    rm -f /tmp/$KEY_ID.pub
fi

# create package dir
if [ ! -d /data/cdimage ]; then
    sudo mkdir /data/cdimage
    sudo chown $USER:$GROUP /data/cdimage
fi

# Report common users' problems in SSH setup
s=`stat -c "%a" ~`
[ $s -gt 755 ] && echo "home dir permissions are wrong: fix with chmod 755 ~"
s=`stat -c "%a" ~/.ssh`
[ $s -gt 700 ] && echo "~/.ssh dir permissions are wrong: fix with chmod 700 ~/.ssh"


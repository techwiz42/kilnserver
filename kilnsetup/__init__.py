import os, subprocess, sys, shutil

class KilnSetup:
  def __init__():
    self.steps = {
      'Installing Apache': self.install_apache,
      'Configuring Apache': self.configure_apache,
      'Configuring Kilnserver to start on boot': self.install_init_scripts,
    }
  
  def run(self):
    for step_desc, step_func in self.steps.items():
      print "%s..." % (step_desc),
      if step_func():
        print 'done.'
      else:
        print 'failed!'
        sys.exit(1)

  def shell_command(self, command):
    try:
      out = subprocess.check_output(command.split(' '))
    except subprocess.CalledProcessError, e:
      return (e.returncode, e.output)
    return (0, out)


  def install_apache():
    code, output = self.shell_command('apt-get -y install apache2 libapache2-mod-wsgi')
    if code != 0:
      print "Command '%s' failed with return code %d and output '%s'" % (command, code, output)
      return False
    return True

  def configure_apache():
    target = '/etc/apache2/sites-available/kilnweb.conf'
    shutil.copyfile('apache-kilnweb.conf', target)
    os.chmod(target, 0644)
    os.chown(target, 0, 0)
    target = '/var/lib/apache2/kilnweb'
    os.makedirs(target)
    shutil.copyfile('kilnweb.wsgi', os.path.join(target, 'kilnweb.wsgi'))
    os.chmod(target, 0644)
    commands = [
      'a2enmod wsgi',
      'a2ensite kilnweb',
      'a2dissite 000-default',
      'service apache2 restart',
    ]
    for command in commands:
      code, output = self.shell_command(command)
      if code != 0:
        print "Command '%s' failed with return code %d and output '%s'" % (command, code, output)
        return False
    return True

  def install_init_scripts():
    target = '/etc/init.d/kilncontroller'
    shutil.copyfile('scripts/kilncontroller', target)
    os.chmod(target, 0755)
    os.chown(target, 0, 0)
    return True

def main():
  if os.geteuid() != 0:
    print 'Please run this script as root.'
    sys.exit(1)
  ks = KilnSetup.new()
  ks.run()

if __name__ == '__main__':
  main()

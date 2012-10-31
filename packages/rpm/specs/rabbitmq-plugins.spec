Name:		rabbitmq-server-plugins
Summary:	RabbitMQ server plugins
Version:	2.6.1
Release:	1
License:	GPLv2
Source0:	http://www.rabbitmq.com/releases/plugins/v%{version}/amqp_client-%{version}.ez
Source1:	http://www.rabbitmq.com/releases/plugins/v%{version}/rabbitmq_stomp-%{version}.ez
URL:		http://www.rabbitmq.com/plugins.html
BuildArch:	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}-root
Requires:	rabbitmq-server = %{version}

%description
RabbitMQ server plugins

%package amqp_client
Summary         : Native Erlang AMQP client for RabbitMQ
Requires        : rabbitmq-server = %{version}

%description amqp_client
RabbitMQ plugin for native Erlang message passing to a broker. 
Stomp plugin depends on it.

%package rabbitmq_stomp
Summary         : STOMP plugin for RabbitMQ
Requires        : rabbitmq-server = %{version}
Requires        : rabbitmq-server-plugins-amqp_client = %{version}
Obsoletes       : rabbitmq-server-plugins-rabbit_stomp

%description rabbitmq_stomp
RabbitMQ plugin for exposing AMQP functionality via the STOMP protocol.

%define plugindir /usr/lib/rabbitmq/lib/rabbitmq_server-%{version}/plugins

%prep
%setup -c -T

%install
rm -rf %{buildroot}
install -d -m 755 %{buildroot}%{plugindir}
cp %{SOURCE0} %{buildroot}%{plugindir}
cp %{SOURCE1} %{buildroot}%{plugindir}

%clean
rm -rf %{buildroot}

%files amqp_client
%defattr(-,root,root)
%{plugindir}/amqp_client-%{version}.ez

%files rabbitmq_stomp
%defattr(-,root,root)
%{plugindir}/rabbitmq_stomp-%{version}.ez

require 'raemon'

module Naily
  class Worker
    include Raemon::Worker

    def start
      super
      start_heartbeat
    end

    def stop
      super
      begin
        @connection.close{ stop_event_machine }
      ensure
        stop_event_machine
      end
    end

    def run
      EM.run do
        initialize_server.run
      end
    end

  private

    def start_heartbeat
      @heartbeat ||= Thread.new do
        sleep 30
        heartbeat!
      end
    end

    def initialize_server
      initialize_amqp
      @server = Naily::Server.new(@channel, @exchange, @delegate, @producer)
    end

    def initialize_amqp
      AMQP.logging = true
      @connection = AMQP.connect(connection_options)
      create_channel
      @exchange = @channel.topic(Naily.config.broker_exchange, :durable => true)
      @producer = Naily::Producer.new(@channel, @exchange)
      @delegate = Naily.config.delegate || Naily::Dispatcher.new(@producer)
    rescue => ex
      Naily.logger.error "Exception during AMQP connection initialization: #{ex}"
      sleep 15
      retry
    end

    def create_channel
      @channel = AMQP::Channel.new(@connection)
      @channel.on_error do |ch, error|
        Naily.logger.fatal "Channel error #{error.inspect}"
        stop
      end
    end

    def connection_options
      {
        :host => Naily.config.broker_host,
        :port => Naily.config.broker_port,
        :username => Naily.config.broker_username,
        :password => Naily.config.broker_password,
      }.reject{|k, v| v.nil? }
    end

    def stop_event_machine
      EM.stop_event_loop if EM.reactor_running?
    end
  end
end
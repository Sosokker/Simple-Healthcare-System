import React, { useEffect, useState } from 'react';
import CardDataStats from '../../components/CardDataStats';
import LineChart from '../../components/Charts/LineChart';
import PieChart from '../../components/Charts/PieChart';
import BarChart from '../../components/Charts/BarChart';
import DefaultLayout from '../../layout/DefaultLayout';
import { FaTemperatureHigh, FaRegLightbulb } from 'react-icons/fa';
import { WiHumidity } from 'react-icons/wi';
import { PiFactoryBold } from 'react-icons/pi';
import { TbBuildingFactory } from 'react-icons/tb';
import {
  fetchWeatherDataList,
  fetchOutdoorWeatherData,
  fetchIndoorWeatherData,
} from '../../api/WeatherData';

const Statistic: React.FC = () => {
  const [weatherDataList, setWeatherDataList] = useState<WeatherData[] | null>(
    null,
  );
  const [outdoorWeatherData, setOutdoorWeatherData] =
    useState<WeatherData | null>(null);
  const [indoorWeatherData, setIndoorWeatherData] =
    useState<IndoorWeatherData | null>(null);
  const days = 10;

  useEffect(() => {
    const fetchData = async () => {
      const weatherList = await fetchWeatherDataList(days);
      setWeatherDataList(weatherList);

      const outdoorWeather = await fetchOutdoorWeatherData(days);
      setOutdoorWeatherData(outdoorWeather);

      const indoorWeather = await fetchIndoorWeatherData(days);
      setIndoorWeatherData(indoorWeather);
    };

    fetchData();
  }, [days]);

  return (
    <DefaultLayout>
      <div className="container mx-auto">
        <h2 className="text-xl font-semibold mb-4">Weekly Average Data</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5">
          <CardDataStats
            title="Outdoor Temperature"
            total={`${outdoorWeatherData?.avg_outdoor_temp.toPrecision(3) ?? '-'} °C`}
            rate="0.43%"
            levelUp
          >
            <FaTemperatureHigh />
          </CardDataStats>
          <CardDataStats
            title="Outdoor Humidity"
            total={`${outdoorWeatherData?.avg_outdoor_humidity ?? '-'} %`}
            rate="4.35%"
            levelUp
          >
            <WiHumidity />
          </CardDataStats>
          <CardDataStats
            title="Outdoor PM2.5"
            total={`${outdoorWeatherData?.avg_outdoor_pm25 ?? '-'} µg/m³`}
            rate="2.59%"
            levelUp
          >
            <PiFactoryBold />
          </CardDataStats>
          <CardDataStats
            title="Outdoor PM10"
            total={`${outdoorWeatherData?.avg_outdoor_pm10 ?? '-'} µg/m³`}
            rate="0.95%"
            levelDown
          >
            <TbBuildingFactory />
          </CardDataStats>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-6 xl:grid-cols-4 2xl:gap-7.5 mt-2">
          <CardDataStats
            title="Indoor Temperature"
            total={`${indoorWeatherData?.avg_indoor_temp ?? '-'} °C`}
            rate="0.43%"
            levelUp
          >
            <FaTemperatureHigh />
          </CardDataStats>
          <CardDataStats
            title="Indoor Light"
            total={`${indoorWeatherData?.avg_indoor_light ?? '-'} Lux`}
            rate="4.35%"
            levelUp
          >
            <FaRegLightbulb />
          </CardDataStats>
        </div>

        <div className="mt-4 grid grid-cols-12 gap-4 md:mt-6 md:gap-6 2xl:mt-7.5 2xl:gap-7.5">
          <LineChart />
          <BarChart />
          <PieChart />
        </div>
      </div>
    </DefaultLayout>
  );
};

export default Statistic;
